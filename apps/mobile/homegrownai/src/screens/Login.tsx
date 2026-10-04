// @ts-ignore
import "../global.css";
import { View, TextInput, Pressable, Text, ActivityIndicator} from 'react-native';
import { useContext, useState } from "react";
import { type StaticScreenProps } from '@react-navigation/native';
import { AuthContext } from '@/contexts';
import { useColorScheme } from 'react-native';
import { useFonts } from '@expo-google-fonts/inter/useFonts';
import { Inter_400Regular, Inter_700Bold } from '@expo-google-fonts/inter';
import HomeGrownAIIcon from "@/components/HomeGrownAIIcon";
import { useNavigation } from '@react-navigation/native';

type LoginScreenProps = StaticScreenProps<{
	wasLoggedIn: boolean;
}>;

export default function LoginScreen({ route }: LoginScreenProps) {
	const [username, setUsername] = useState("");
	const [password, setPassword] = useState("");
	const navigation = useNavigation();
	let colorScheme = useColorScheme();

	// @ts-ignore
	const { signIn } = useContext(AuthContext);

	let [fontsLoaded] = useFonts({
		Inter_400Regular,
		Inter_700Bold
	});


	if (!fontsLoaded) {
		return (<></>);
	} else {
		return (
			<View className="flex-1 justify-center items-center h-screen">
			{!fontsLoaded ? <ActivityIndicator size="large"/> : <><HomeGrownAIIcon/>
				<TextInput className="border-blue-400 border w-1/2 text-lg mt-7 rounded-md p-0.5" style={{fontFamily: "Inter_400Regular"}} editable value={username} placeholder="Username" placeholderTextColor={"#D3D3D3"} onChangeText={setUsername} multiline={false} autoComplete={"username"} clearButtonMode='always' defaultValue='username'/>
				<TextInput className="border-blue-400 border w-1/2 text-lg mt-3 rounded-md p-0.5" style={{fontFamily: "Inter_400Regular"}} editable secureTextEntry value={password} placeholder="Password" placeholderTextColor={"#D3D3D3"} onChangeText={setPassword} multiline={false} autoComplete={"current-password"} clearButtonMode='always' defaultValue='password'/>
				<View>
					<Pressable onPressOut={() => signIn({ username, password})} className="w-1/2 rounded-full mt-3 bg-blue-100">
						<Text style={{fontFamily: "Inter_400Regular"}} className="text-xl ml-4 mr-4 p-2">Login</Text>
					</Pressable>
				</View>
				<View className="flex-row absolute bottom-6">
					<Text style={{fontFamily:'Inter_400Regular'}}>Don't have an account yet? </Text>
					<Pressable onPressOut={() => navigation.navigate('SignUp', {})}>
						<Text style={{fontFamily: "Inter_700Bold"}} className="underline text-blue-500">Sign Up!</Text>
					</Pressable>
				</View></>}

			</View>
		);
	}
};
