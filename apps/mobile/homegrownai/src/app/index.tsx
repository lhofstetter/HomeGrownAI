// import * as Device from 'expo-device';
// import { GestureResponderEvent, Platform, Pressable, StyleSheet, TextInput, useColorScheme, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
// import { useState } from 'react';
import uuid from 'react-native-uuid';

import Chat from '@/components/Chat';

export default function Home() {
	return (
		<SafeAreaProvider>
			<Chat conversationTitle='New Chat' conversationID={uuid.v4()}/>
		</SafeAreaProvider>
	);
}
