// @ts-ignore
import "../global.css";
import { View, TextInput, Pressable, Text, Alert } from 'react-native';
import { useContext, useState } from "react";
import { type StaticScreenProps } from '@react-navigation/native';
import { AuthContext } from '@/contexts';
import { Appearance, useColorScheme } from 'react-native';


type LoginScreenProps = StaticScreenProps<{
	wasLoggedIn: boolean;
}>;

export default function LoginScreen({ route }: LoginScreenProps) {
	const [username, setUsername] = useState("");
	const [password, setPassword] = useState("");
	let colorScheme = useColorScheme();

	// @ts-ignore
	const { signIn } = useContext(AuthContext);

	return (
		<View className="flex flex-col items-center">
			<TextInput className="border-blue-400 border-2 w-1/2 text-lg mt-7 rounded-md" editable value={username} onChangeText={setUsername} multiline={false} autoComplete={"username"} clearButtonMode='always' defaultValue='username'/>
			<View/>
			<TextInput className="border-blue-400 border-2 w-1/2 text-lg mt-5 rounded-md" editable secureTextEntry value={password} onChangeText={setPassword} multiline={false} autoComplete={"current-password"} clearButtonMode='always' defaultValue='password'/>
			<View>
				<Pressable onPressOut={() => signIn({ username, password})} className="border-blue-400 border-2 w-1/2 rounded-md mt-2 bg-blue-100">
					<Text>Login</Text>
				</Pressable>
				<Text></Text>
			</View>
		</View>
	);
};
