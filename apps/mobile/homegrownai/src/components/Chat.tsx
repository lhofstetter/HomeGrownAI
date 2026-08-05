import { useState } from "react";
import { GestureResponderEvent, Pressable, TextInput, useColorScheme, FlatList, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import uuid from 'react-native-uuid';

import ChatProps from "@/types/ChatProps";
import Sender from "@/types/sender";
import Message from "@/types/chatMessage";
import { ThemedView } from "./themed-view";
import { ArrowCircleUpBlackIcon, ArrowCircleUpWhiteIcon } from "./ArrowCircleUpIcon";
import ChatMessage from "./ChatMessage";

export default function Chat({conversationTitle, conversationID, modelID, attachments}: ChatProps) {
	const colorScheme = useColorScheme();

	const sender: Sender = {
		id: "default"
	};
	const [chat, addToChat] = useState<Message[]>([]);
	const [currentMessage, addToCurrentMessage] = useState<Message>({
		senderId: sender,
		message: "",
		id: uuid.v4()
	});

	function appendToMessage(messageText: string) {
		addToCurrentMessage({
			senderId: sender,
			message: messageText,
			id: currentMessage.id
		});
	}
	
	function onSubmit(event: GestureResponderEvent) {
		addToChat([...chat, currentMessage]);
		addToCurrentMessage({
			senderId: sender,
			message: "",
			id: uuid.v4()
		});
	}

	return (
			<SafeAreaView style={{ flex: 1 }}>
				<ThemedView className="flex-1">
					<FlatList ItemSeparatorComponent={() => <View className="h-2 m-4"/>} style={{ flex: 1 }} contentContainerStyle={{flexGrow: 1, justifyContent: "flex-end", paddingHorizontal: 16, paddingVertical: 8, marginBottom: "8%"}} data={chat} renderItem={({ item }) => (<ChatMessage key={item.id} message={item} side={item.senderId.id !== "model" ? "right" : "left"}/>)} keyExtractor={(item) => item.id.toString()}/>
					<ThemedView className="flex-row grow-0 items-center gap-2 border-t border-slate-300 px-4 py-3 dark:border-slate-700">
						<TextInput editable multiline onChangeText={(value) => appendToMessage(value)} value={currentMessage.message} className="min-h-12 flex-1 rounded-full border border-slate-600 px-4 py-3 text-black dark:text-white"/>
						<Pressable onPress={onSubmit} className="items-center justify-center">
							{colorScheme === "light" ? <ArrowCircleUpBlackIcon size={36}/> : <ArrowCircleUpWhiteIcon size={36}/>}
						</Pressable>
					</ThemedView>
				</ThemedView>
			</SafeAreaView>
	);
}
