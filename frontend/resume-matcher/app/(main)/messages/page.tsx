"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Send, Loader2, MessageCircle, ArrowLeft } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { 
  getConversations, 
  getMessagesWithUser, 
  sendMessage, 
  markConversationAsRead,
  ConversationResponse,
  MessageResponse
} from "@/lib/api";

export default function MessagesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [conversations, setConversations] = useState<ConversationResponse[]>([]);
  const [activeUser, setActiveUser] = useState<{ id: number, name: string } | null>(null);
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollingInterval = useRef<NodeJS.Timeout | null>(null);

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
    loadConversations();
    
    const userId = searchParams.get('userId');
    const userName = searchParams.get('userName');
    
    if (userId && userName) {
      setActiveUser({ id: parseInt(userId), name: userName });
    }
    
    pollingInterval.current = setInterval(() => {
      loadConversations(true);
      if (activeUser) {
        loadMessages(activeUser.id, true);
      }
    }, 10000);
    
    return () => {
      if (pollingInterval.current) clearInterval(pollingInterval.current);
    };
  }, [searchParams, loadConversations, activeUser, loadMessages]);

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
        job_id: null,
        content: newMessage,
        is_read: false,
        created_at: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, tempMessage]);
      setNewMessage("");
      
      const sentMessage = await sendMessage(token, activeUser.id, tempMessage.content);
      
      setMessages(prev => prev.map(m => m.id === tempMessage.id ? sentMessage : m));
      
      await loadConversations(false);
      
    } catch (error) {
      console.error(error);
      alert("Mesaj gönderilemedi");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <div className="bg-white border-b px-6 py-4 flex items-center gap-4">
        <button 
          onClick={() => router.back()} 
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold">Mesajlar</h1>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-80 border-r bg-white flex flex-col">
          <div className="p-4 border-b">
            <h2 className="font-semibold text-lg">Konuşmalar</h2>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {isLoadingConversations ? (
              <div className="flex justify-center p-8">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : conversations.length === 0 ? (
              <div className="p-6 text-center text-sm text-gray-500">
                Henüz mesajınız yok
              </div>
            ) : (
              conversations.map((conv) => (
                <div 
                  key={conv.other_user_id}
                  onClick={() => setActiveUser({ id: conv.other_user_id, name: conv.other_user_name })}
                  className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition-colors ${
                    activeUser?.id === conv.other_user_id ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                  }`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-semibold truncate">{conv.other_user_name}</span>
                    {conv.unread_count > 0 && (
                      <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 truncate">{conv.last_message}</p>
                </div>
              ))
            )}
          </div>
        </div>
        
        <div className="flex-1 flex flex-col bg-white">
          {activeUser ? (
            <>
              <div className="p-4 border-b bg-white">
                <h3 className="font-semibold text-lg">{activeUser.name}</h3>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
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
                    const currentUserId = parseInt(localStorage.getItem("userId") || "0");
                    const isMine = msg.sender_id === currentUserId;
                    
                    return (
                      <div 
                        key={msg.id} 
                        className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}
                      >
                        <div 
                          className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                            isMine 
                              ? 'bg-blue-600 text-white' 
                              : 'bg-white text-gray-800 border'
                          }`}
                        >
                          <p className="text-sm">{msg.content}</p>
                          <div className={`text-xs mt-1 ${isMine ? 'text-blue-100' : 'text-gray-400'}`}>
                            {new Date(msg.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </div>
              
              <div className="p-4 bg-white border-t">
                <form onSubmit={handleSendMessage} className="flex gap-3">
                  <textarea
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Mesaj yazın..."
                    className="flex-1 resize-none border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-xl px-6 py-3 transition-colors"
                  >
                    {isSending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center text-gray-400">
              <MessageCircle className="w-20 h-20 mb-4 opacity-20" />
              <p className="text-lg">Soldan bir konuşma seçin</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
