import ChatMessage from '@/types/chatMessage';

interface ChatMessageProps {
	message: ChatMessage;
	side?: string;
	expandable?: boolean;
}

export default ChatMessageProps;
