"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { X, Send, Loader2, MessageCircle } from "lucide-react";
import { 
  getConversations, 
  getMessagesWithUser, 
  sendMessage, 
  markConversationAsRead,
  ConversationResponse,
  MessageResponse
} from "@/lib/api";

interface MessagesDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  targetUserId?: number | null;
  targetUserName?: string;
  initialMessage?: string;
  targetJobId?: number | null;
}

export default function MessagesDrawer({
  isOpen,
  onClose,
  targetUserId,
  targetUserName,
  initialMessage,
  targetJobId
}: MessagesDrawerProps) {
  const [conversations, setConversations] = useState<ConversationResponse[]>([]);
  const [activeUser, setActiveUser] = useState<{ id: number, name: string } | null>(null);
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);
  const [newMessage, setNewMessage] = useState("");
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollingInterval = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      const token = localStorage.getItem("accessToken");
      if (!token) return;
      try {
        const response = await fetch("https://ai-cv-matcher-5sui.onrender.com/api/v1/users/me", {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          const user = await response.json();
          setCurrentUserId(user.id);
        }
      } catch (error) {
        console.error('Error fetching current user:', error);
      }
    };
    fetchCurrentUser();
  }, []);

  const loadConversations = useCallback(async (silent = false) => {
    try {
      if (!silent) setIsLoadingConversations(true);
      const token = localStorage.getItem("accessToken");
      if (!token) return;
      const data = await getConversations(token);
      setConversations(data);
    } catch (error) {
      console.error('Error loading conversations:', error);
    } finally {
      setIsLoadingConversations(false);
    }
  }, []);

  const loadMessages = useCallback(async (userId: number, silent = false) => {
    try {
      if (!silent) setIsLoadingMessages(true);
      const token = localStorage.getItem("accessToken");
      if (!token) return;
      
      const data = await getMessagesWithUser(token, userId);
      setMessages(data);
      
      await markConversationAsRead(token, userId);
      if (!silent) loadConversations(true);
    } catch (error) {
      console.error('Error loading messages:', error);
      setMessages([]);
    } finally {
      setIsLoadingMessages(false);
    }
  }, [loadConversations]);

  useEffect(() => {
    if (isOpen) {
      loadConversations();
      
      if (targetUserId && targetUserName) {
        setActiveUser({ id: targetUserId, name: targetUserName });
        if (initialMessage) {
          setNewMessage(initialMessage);
        }
      }
      
      pollingInterval.current = setInterval(() => {
        loadConversations(true);
      }, 10000);
    } else {
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
      }
      setActiveUser(null);
      setMessages([]);
    }
    
    return () => {
      if (pollingInterval.current) clearInterval(pollingInterval.current);
    };
  }, [isOpen, targetUserId, targetUserName, initialMessage, loadConversations]);

  useEffect(() => {
    if (activeUser) {
      loadMessages(activeUser.id);
    } else {
      setMessages([]);
    }
  }, [activeUser, loadMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !activeUser) return;
    
    try {
      setIsSending(true);
      const token = localStorage.getItem("accessToken");
      if (!token) return;
      
      const tempMessage: MessageResponse = {
        id: Date.now(),
        sender_id: -1,
        receiver_id: activeUser.id,
        job_id: targetJobId || null,
        content: newMessage,
        is_read: false,
        created_at: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, tempMessage]);
      setNewMessage("");
      
      const sentMessage = await sendMessage(token, activeUser.id, tempMessage.content, targetJobId || undefined);
      
      setMessages(prev => prev.map(m => m.id === tempMessage.id ? sentMessage : m));
      
      await loadConversations(false);
      
    } catch (error) {
      console.error(error);
      alert("Mesaj gönderilemedi");
    } finally {
      setIsSending(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/50 z-[100] transition-opacity"
        onClick={onClose}
      />
      
      <div className="fixed top-0 right-0 h-full w-[700px] bg-white shadow-2xl z-[110]">
        <div className="h-full flex">
          <div className="w-[250px] border-r h-full flex flex-col bg-gray-50">
            <div className="p-4 border-b bg-white">
              <h2 className="font-semibold text-base">Mesajlar</h2>
            </div>
            
            <div className="flex-1 overflow-y-auto">
              {isLoadingConversations ? (
                <div className="flex justify-center p-4">
                  <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                </div>
              ) : conversations.length === 0 ? (
                <div className="p-4 text-center text-xs text-gray-500">
                  Henüz mesaj yok
                </div>
              ) : (
                conversations.map((conv) => (
                  <div 
                    key={conv.other_user_id}
                    onClick={() => setActiveUser({ id: conv.other_user_id, name: conv.other_user_name })}
                    className={`p-4 border-b cursor-pointer hover:bg-gray-100 transition-colors ${
                      activeUser?.id === conv.other_user_id ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                    }`}
                  >
                    <div className="font-semibold text-base truncate">{conv.other_user_name}</div>
                    <p className="text-sm text-gray-500 truncate mt-1">{conv.last_message}</p>
                  </div>
                ))
              )}
            </div>
          </div>
          
          <div className="flex-1 h-full flex flex-col bg-gray-50">
            {activeUser ? (
              <>
                <div className="p-4 border-b bg-white flex justify-between items-center">
                  <h3 className="font-semibold">{activeUser.name}</h3>
                  <button onClick={onClose} className="text-gray-500 hover:text-black p-1">
                    <X className="w-5 h-5" />
                  </button>
                </div>
                
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {isLoadingMessages ? (
                    <div className="flex justify-center p-8">
                      <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                    </div>
                  ) : messages.length === 0 ? (
                    <div className="text-center text-sm text-gray-500 pt-10">
                      Sohbeti başlatın
                    </div>
                  ) : (
                    messages.map(msg => {
                      const isMine = currentUserId ? msg.sender_id === currentUserId : msg.sender_id !== activeUser.id;
                      
                      return (
                        <div 
                          key={msg.id} 
                          className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}
                        >
                          <div 
                            className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                              isMine 
                                ? 'bg-blue-600 text-white' 
                                : 'bg-white text-gray-800 border'
                            }`}
                          >
                            <p>{msg.content}</p>
                            <div className={`text-[10px] mt-1 ${isMine ? 'text-blue-100' : 'text-gray-400'}`}>
                              {new Date(msg.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                            </div>
                          </div>
                        </div>
                      );
                    })
                  )}
                  <div ref={messagesEndRef} />
                </div>
                
                <div className="p-3 bg-white border-t">
                  <form onSubmit={handleSendMessage} className="flex gap-2">
                    <textarea
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="Mesaj yazın..."
                      className="flex-1 resize-none border rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                      rows={2}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage(e);
                        }
                      }}
                    />
                    <button 
                      type="submit"
                      disabled={!newMessage.trim() || isSending}
                      className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-xl p-3"
                    >
                      {isSending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                    </button>
                  </form>
                </div>
              </>
            ) : (
              <div className="flex flex-1 flex-col items-center justify-center text-gray-400 p-8 text-center">
                <MessageCircle className="w-16 h-16 mb-4 opacity-20" />
                <p>Soldan bir kişi seçin</p>
                <button 
                  onClick={onClose} 
                  className="absolute top-4 right-4 text-gray-500 hover:text-black"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
