import ChatMessageProps from '@/types/ChatMessageProps';
import { useState } from 'react';
import { ThemedView } from './themed-view';
import { Text, useColorScheme } from 'react-native';

export default function ChatMessage({ message, side, expandable }: ChatMessageProps) {
	const theme = useColorScheme();

	return (
		<ThemedView className={side === "right" ? "w-full items-end" : "w-full items-start"}>
			<ThemedView className={ side === "right" ? "absolute right-0 border rounded-2xl bg-gray-400 p-1" : "absolute left-0 border rounded-2xl bg-gray-400 p-1"}>
				<Text className={"font-mono " +  theme === "dark" ? "text-white text-lg" : "text-black text-lg" }>
					{ message.message }
				</Text>
			</ThemedView>
		</ThemedView>
	);
}


