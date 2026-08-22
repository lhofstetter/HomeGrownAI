import { useState, useEffect } from 'react';
import type { StaticScreenProps } from '@react-navigation/native';
import axios from 'axios';
import uuid from 'react-native-uuid';
import * as SecureStore from 'expo-secure-store';

import { SITE } from '@/constants/app';
import Chat from '@/components/Chat';

type HomeScreenProps = StaticScreenProps<{
	token: string;
}>;


export default function HomeScreen({ route }: HomeScreenProps) {
	const [storedToken, setStoredToken] = useState(route.params.token);
	const [loggedIn, setLoggedIn] = useState(false);

	const apiClient = axios.create({
		baseURL: SITE.toString(),
		headers: {
			'Authorization': 'Bearer ' + storedToken,
			'Accept': 'application/json'
		}
	});


	return (
		<>
		{ loggedIn === false ? <></> : <Chat conversationTitle="New Conversation" conversationID={uuid.v4()}/> }
		</>
	);
};
