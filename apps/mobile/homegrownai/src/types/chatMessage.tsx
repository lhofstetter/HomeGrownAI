import Sender from '@/types/sender';

type Message = {
	id: string;
	message: string;
	senderId: Sender; 
};

export default Message;
