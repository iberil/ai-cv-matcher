from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func
from typing import List

from ...core.database import get_db
from ...models.user import User
from ...models.message import Message
from ...models.notification import Notification
from ...schemas.message_schemas import MessageCreate, MessageResponse, ConversationResponse
from .auth import get_current_active_user
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=MessageResponse)
def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Yeni bir mesaj gönderir.
    """
    if current_user.id == message_data.receiver_id:
        raise HTTPException(status_code=400, detail="Kendinize mesaj gönderemezsiniz.")
        
    # Alıcıyı kontrol et
    receiver = db.query(User).filter(User.id == message_data.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Alıcı bulunamadı.")
        
    db_message = Message(
        sender_id=current_user.id,
        receiver_id=message_data.receiver_id,
        job_id=message_data.job_id,
        content=message_data.content,
        is_read=False
    )
    
    db.add(db_message)
    
    # Bildirim oluştur
    notification = Notification(
        user_id=message_data.receiver_id,
        title="Yeni Mesaj",
        message=f"{current_user.full_name} size bir mesaj gönderdi.",
        type="info",
        is_read=False
    )
    db.add(notification)
    
    db.commit()
    db.refresh(db_message)
    return db_message

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcının aktif mesajlaşmalarını listeler.
    Her kişi(other_user) için son mesaj, okunmamış mesaj sayısı vb. döndürülür.
    """
    conversations = []
    
    # Kullanıcının iletişim kurduğu kişilerin ID'lerini bul
    sent_ids = db.query(Message.receiver_id).filter(
        Message.sender_id == current_user.id
    ).distinct().all()
    received_ids = db.query(Message.sender_id).filter(
        Message.receiver_id == current_user.id
    ).distinct().all()
    
    # Tüm unique iletişim kurulan kullanıcı ID'leri
    contact_ids = set([r[0] for r in sent_ids] + [r[0] for r in received_ids])
    contact_ids.discard(None)  # None değerlerini temizle
    
    for contact_id in contact_ids:
        # Karşıdaki kullanıcı bilgisi
        other_user = db.query(User).filter(User.id == contact_id).first()
        if not other_user:
            continue
            
        # Bu iki kişi arasındaki son mesaj
        last_message = db.query(Message).filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == contact_id),
                and_(Message.sender_id == contact_id, Message.receiver_id == current_user.id)
            )
        ).order_by(desc(Message.created_at)).first()
        
        # Okunmamış mesaj sayısı (sadece karşıdan gelenler)
        unread_count = db.query(Message).filter(
            Message.sender_id == contact_id,
            Message.receiver_id == current_user.id,
            Message.is_read == False
        ).count()
        
        conversations.append(ConversationResponse(
            other_user_id=contact_id,
            other_user_name=other_user.full_name,
            last_message=last_message.content if last_message else "",
            last_message_at=last_message.created_at if last_message else None,
            unread_count=unread_count
        ))
        
    # En son mesajlaşılana göre sırala (None güvenli)
    def sort_key(conv):
        return conv.last_message_at.replace(tzinfo=None) if conv.last_message_at else datetime.min

    conversations.sort(key=sort_key, reverse=True)
    return conversations

@router.get("/conversation/{other_user_id}", response_model=List[MessageResponse])
def get_messages_with_user(
    other_user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Belirli bir kişiyle olan tüm mesajları getir.
    """
    messages = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at).all()
    
    return messages

@router.put("/conversation/{other_user_id}/read")
def mark_conversation_as_read(
    other_user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Belirli birinden gelen tüm mesajları okundu olarak işaretler.
    """
    unread_messages = db.query(Message).filter(
        Message.sender_id == other_user_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
        
    db.commit()
    return {"status": "success", "marked_read": len(unread_messages)}
