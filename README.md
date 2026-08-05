# HomeGrownAI App

This repository is home to a pet project of mine, which is to try to *recreate as close to a ChatGPT-like experience as possible using only self-hosted, open-weight models*.

My plan for the repository is to keep it open-source as it's developed, not just because I want to say I did it and have proof, but because I want other poeple to be able to build with me (if they desire), learn from my mistakes and maybe even learn a few new things along the way (though... idk there's a lot smarter people than me that work on stuff like this so probably not but you never know!)

## Q & A

### Why do this anyways? Hasn't it already been done a million times?

Excellent question!

While partially to gain experience with various frameworks and construct a user-facing, real-world application from the ground up, this also scratches a personal itch of mine: how much of the intelligence and capability of modern models comes from the model itself, and how much comes from the supporting infrastructure around it (intelligent use of context windows, RAG pipelines, steering outputs and re-generating, etc)?

While most people would answer that it's obviously the model, I'm personally not so sure. One set of tests on the latest and greatest model from Anthropic (Fable 5) shows that it actually lands [pretty middle of the road when it comes to fixing vulnerabilities](https://www.endorlabs.com/learn/claude-fable-5-mythos-grade-hype). Additionally, a predeployment evaluation of GPT-5.6 Sol finds that the model "cheats" at a [much higher rate than any other previously evaluated model](https://metr.org/blog/2026-06-26-gpt-5-6-sol/). Therefore, I find myself wondering how much the newest models are drastically improving, and how much their harnesses and support systems are improving. While there is no doubt the model drives major improvement, I personally wish to understand for myself how much benefit you can get when targeting just the harness and pipelines BEFORE improving the model.

### What technologies are you using? 

HomeGrownAI currently utilizes the languages and frameworks below for the project's various components:

#### Backend
**Language**: Python 
**Frameworks/Libraries**:
* FastAPI 
* Pydantic
* SQLAlchemy
* Hypercorn
* psycopg
* Alembic
* Loguru
* pwdlib
* pyjwt
* uvloop
* asyncio
**Tools**:
* uv
* ty

For the backend, I use FastAPI for ease of use and Hypercorn for it's HTTP/2 and 3 capabilities, coupled with uvloop/asyncio. While using Hypercorn over Uvicorn wouldn't matter if the application was parked behind a reverse proxy, I like the newer protocol support being native. Pydantic is used for data validation and signup/signin with Bearer Tokens, with pyjwt being used for the Bearer Tokens themselves. Database interfacing uses SQLAlchemy with the psycopg adapter, since I chose to use PostgreSQL. Alembic is used for database migrations, and pwdlib is used for password salt + hashing.

For AI/LLM, I'm thinking of using vLLM due to it's performance in terms of raw throughput. However, I may use SGLang or other frameworks depending on how difficult it is to wire-up agentic capabilities with vLLM as the project grows.

       
#### Mobile
**Language**: Primarily TypeScript, with a smidge of JavaScript 
**Frameworks/Libraries**:
* React/React Native 
* Expo
* react-native-uuid
* Nativewind/TailwindCSS
**Tools**: 
* [Bun](https://bun.com)

So far, the set of used libraries/components is pretty basic, as I'm mainly focused on getting the basic MVP up and running. I'll soon add the network dependencies required to communicate with the backend and more advanced functionality, but I want to get the actual LLM portion done on the backend so that I can test the chat functionality. 

#### Web 
**Language**: Primarily TypeScript, with a smidge of JavaScript 
**Frameworks/Libraries**:
* React 
* Vite
**Tools**: 
* [Bun](https://bun.com)

I've done nothing on this so far - my focus is on the backend and mobile app for now. I'll be fleshing out the web once I have a better feel for the UI from the app and which parts make sense on the web/what specific niches the web code will need to fulfill that the mobile app code can't, won't or shouldn't. 
