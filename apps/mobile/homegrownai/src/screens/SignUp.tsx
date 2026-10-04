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

type SignUpScreenProps = StaticScreenProps<{}>;

export default function SignUpScreen({ route }: SignUpScreenProps) {
	const [username, setUsername] = useState("");
	const [emailAddress, setEmailAddress] = useState("");
	const [password, setPassword] = useState("");
	const [confirmPassword, setConfirmPassword] = useState("");

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
			{!fontsLoaded ? <ActivityIndicator size="large"/> : <>
				<HomeGrownAIIcon/>
				<View className="flex-row">
					<Text style={{fontFamily: "Inter_700Bold"}} className="text-lg">Username: </Text>
					<TextInput className="border-blue-400 border w-1/2 text-lg rounded-md" style={{fontFamily: "Inter_400Regular"}} editable value={username} placeholder="Username" placeholderTextColor={"#D3D3D3"} onChangeText={setUsername} multiline={false} autoComplete={"username"} clearButtonMode='always' defaultValue='username'/>
				</View>
				<View className="flex-row mt-3 -left-4">
					<Text style={{fontFamily: "Inter_700Bold"}} className="text-lg">Email Address: </Text>
					<TextInput className="border-blue-400 border w-1/2 text-lg rounded-md" style={{fontFamily: "Inter_400Regular"}} editable value={emailAddress} placeholder="Email Address" placeholderTextColor={"#D3D3D3"} onChangeText={setEmailAddress} multiline={false} autoComplete={"email"} clearButtonMode='always'/>
				</View>
				<View className="flex-row mt-3">
					<Text style={{fontFamily: "Inter_700Bold"}} className="text-lg">Password: </Text>
					<TextInput className="border-blue-400 border w-1/2 text-lg rounded-md -right-1" style={{fontFamily: "Inter_400Regular"}} editable secureTextEntry value={password} placeholder="Password" placeholderTextColor={"#D3D3D3"} onChangeText={setPassword} multiline={false} autoComplete={"current-password"} clearButtonMode='always' defaultValue='password'/>
				</View>
				<View className="flex-row mt-3 -left-9">
					<Text style={{fontFamily: "Inter_700Bold"}} className="text-lg">Confirm Password: </Text>
					<TextInput className="border-blue-400 border w-1/2 text-lg rounded-md" style={{fontFamily: "Inter_400Regular"}} editable secureTextEntry value={confirmPassword} placeholder="Password" placeholderTextColor={"#D3D3D3"} onChangeText={setConfirmPassword} multiline={false} autoComplete={"current-password"} clearButtonMode='always' defaultValue='password'/>
				</View>
				<View className="mt-3">
					<Pressable onPressOut={() => signIn({ username, password})} className="w-1/2 rounded-full mt-3 bg-blue-100">
						<Text style={{fontFamily: "Inter_400Regular"}} className="text-xl ml-4 mr-4 p-2">Sign Up</Text>
					</Pressable>
				</View>
				</>}

			</View>
		);
	}
};
