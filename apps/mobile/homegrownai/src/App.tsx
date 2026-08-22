import { createStaticNavigation } from '@react-navigation/native';
import {
  createNativeStackNavigator,
} from '@react-navigation/native-stack';
import { useContext, createContext, useReducer, useMemo } from 'react';
import HomeScreen from '@/screens/Home';
import LoginScreen from '@/screens/Login';
import * as SecureStore from 'expo-secure-store';
import { SITE } from '@/constants/app';
import Animated, { useSharedValue, useAnimatedProps, withRepeat, withTiming, Easing } from 'react-native-reanimated';
import { MeshGradientView } from 'expo-mesh-gradient';
import { useEffect } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import * as Crypto from 'expo-crypto';
import SignInForm from './types/SignInForm';
import axios, { AxiosError } from 'axios';
import { AuthContext, SignInContext } from './contexts';

const AnimatedMeshGradient = Animated.createAnimatedComponent(MeshGradientView);

function SplashScreen() {
	const centerX = useSharedValue(0.5);
	const centerY = useSharedValue(0.5);

	useEffect(() => {
    centerX.value = withRepeat(
      withTiming(0.7, { duration: 3000, easing: Easing.inOut(Easing.ease) }),
      -1,
      true
    );
    centerY.value = withRepeat(
      withTiming(0.3, { duration: 4000, easing: Easing.inOut(Easing.ease) }),
      -1,
      true
    );
  }, []);

  const animatedProps = useAnimatedProps(() => {
    return {
      points: [
        [0.0, 0.0], [0.5, 0.0], [1.0, 0.0],
        [0.0, 0.5], [centerX.value, centerY.value], [1.0, 0.5],
        [0.0, 1.0], [0.5, 1.0], [1.0, 1.0],
      ] as [number, number][],
    };
  });

  return (
    <View style={{flex: 1}}>
      <AnimatedMeshGradient
        style={StyleSheet.absoluteFill}
        columns={3}
        rows={3}
        colors={[
          '#ff007f', '#7f00ff', '#00ffff',
          '#ffaa00', '#ffffff', '#00ffaa',
          '#0000ff', '#990022', '#33ff33'
        ]}
        animatedProps={animatedProps}
      />
    </View>
  );

};

const isSignedIn = () => {
	const access_token = SecureStore.getItem("access_token");

	if (access_token === null) {
		return false;
	}

	const apiClient = axios.create({
		baseURL: SITE.toString(),
		headers: {
			'Authorization': 'Bearer ' + access_token,
			'Accept': 'application/json'
		}
	});

	let return_status: boolean = false;

	apiClient.get('users/conversations').then(response => {
		if (response.status === 401) { // means the token is expired
			return_status = false;
		} else {
			return_status = true;
		}
	});

	return return_status;
};

function routeIsSignedIn() {
	const isSignedIn = useContext(SignInContext);
	return isSignedIn;
}

function routeIsSignedOut() {
	return !routeIsSignedIn();
}


const RootStack = createNativeStackNavigator({
  screens: {
    Home: {
		if: routeIsSignedIn,
		screen: HomeScreen,
    },
	Login: {
		if: routeIsSignedOut,
		screen: LoginScreen,
	},
  },
});

const Navigation = createStaticNavigation(RootStack);

export default function App() {
	const [state, dispatch] = useReducer(
		(prevState: any, action) => {
			switch (action.type) {
				case 'CACHED_TOKEN':
					return {
						authToken: action.authToken,
						isLoading: false,
						signingUp: false,
					};
				case 'SIGN_IN':
					return {
						authToken: action.authToken,
						isSignedOut: false,
						signingUp: false,
					};
				case 'SIGN_UP':
					return {
						isSignedOut: true,
						authToken: null,
						signingUp: true,
					}
				case 'SIGN_OUT':
					return {
						isSignedOut: true,
						authToken: null,
						signingUp: false,
					};
			}
		},
		{
			isLoading: true,
			isSignedOut: false,
			authToken: null,
			signingUp: false,
		});

		useEffect(() => {
			const verifySignIn = async () => {
				let authToken = await SecureStore.getItemAsync('access_token');

				if (authToken != null) {
					const apiClient = axios.create({
						baseURL: SITE.toString(),
						headers: {
							'Authorization': 'Bearer ' + authToken,
							'Accept': 'application/json'
						}
					});

					try {
						const conversations = await apiClient.get("users/conversations");

						// implement later - would be useful to have this in a global app store that is persistent across screens without
						// being passed everywhere or stored in SecureStore (since it doesn't need to be and I don't think SecureStore works
						// with values that big...
						dispatch({type: 'CACHED_TOKEN', token: authToken, isLoading: false});
					} catch (error) { // auth token is expired
						dispatch({ type: 'SIGN_OUT', isLoading: false});
					}
				} else {
					dispatch({ type: 'SIGN_OUT', isLoading: false});
				}
			};

			verifySignIn();
		}, []);

	const authContext = useMemo(() => ({
		signIn: async (data: SignInForm) => {
			const loginFormData = new FormData();

			const passwordDigest = await Crypto.digestStringAsync(Crypto.CryptoDigestAlgorithm.SHA512, data.password);

			loginFormData.append('username', data.username);
			loginFormData.append('password', passwordDigest);
			const apiClient = axios.create({
				baseURL: SITE.toString(),
				headers: {
					'Accept': 'application/json'
				} });

			try {
				const loginResponse = await apiClient.postForm("users/login", loginFormData);
				await SecureStore.setItemAsync("access_token", loginResponse.data.access_token);

	        	dispatch({ type: 'SIGN_IN', token: loginResponse.data.access_token, isLoading: false });
			} catch (error: any) {
				console.log(error.message, error.code, error.status);
				Alert.alert("Incorrect Username/email address or Password", "Please enter a valid username or email address and password.", [
					{
						text: "OK",
						onPress: () => {},
					}
				]);
			}

	},
		signOut: () => dispatch({ type: 'SIGN_OUT', isLoading: false }),
		signUp: () => dispatch({ type: 'SIGN_UP', signingUp: true, isLoading: false }),
	}), []);

	if (state.isLoading) {
		return <SplashScreen/>;
	}

	const isSignedIn = state.authToken != null;


  return (
	<AuthContext.Provider value={authContext}>
		<SignInContext.Provider value={isSignedIn}>
			<Navigation/>
		</SignInContext.Provider>
	</AuthContext.Provider>
  );
}

type RootStackType = typeof RootStack;

declare module '@react-navigation/native' {
  interface RootNavigator extends RootStackType {}
}
