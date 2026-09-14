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
<br/>
**Frameworks/Libraries**:
* FastAPI
* Pydantic
* SQLAlchemy
* Uvicorn
* psycopg
* Alembic
* Loguru
* pwdlib
* pyjwt
* uvloop
* asyncio
* vLLM
* bitsandbytes
* huggingface
* niquests
* markitdown
* Wenmode
* docker
<br/>
**Tools**:
* uv
* ty
* Docker
<br/>
For the backend, I use FastAPI for ease of use and Uvicorn for it's superior HTTP 1/1.1 throughput (as the application is designed to be put behind a reverse proxy), coupled with uvloop/asyncio. Pydantic is used for data validation and signup/signin with Bearer Tokens, with pyjwt being used for the Bearer Tokens themselves. Database interfacing uses SQLAlchemy with the psycopg adapter, since I chose to use PostgreSQL. Alembic is used for database migrations, and pwdlib is used for password salt + hashing.

For AI/LLM, I currently utilize vLLM due to it's speed, vast hardware support and ease of integration with common quantization technologies (such as bitsandbytes which is used for 4-bit quantization). vLLM-Metal is also used to support macOS devices, which requires Python 3.12 for now. Obscura is used for a "stealth" browser tool that can run persistently as it's own process, while Playwright + CDP is used to control it. Docker is used to launch and control [Degoog](https://github.com/degoog-org/degoog), which is a self-hosted search engine aggregator that provides an API for the backend to use for searching. In the future, I'll document more of what works and what doesn't for the AI/LLM portions, as I know that (for me personally) it is difficult to see what does and doesn't work amongst today's documentation.

#### Mobile
**Language**: Primarily TypeScript, with a smidge of JavaScript
<br/>
**Frameworks/Libraries**:
* React/React Native
* Expo
* React Navigation
* react-native-uuid
* Nativewind/TailwindCSS
* Axios
<br/>
**Tools**:
* [Bun](https://bun.com)
<br/>
I utilize React/React Native due to the familiarity and experience I have with it when helping to develop [cinder](https://github.com/lhofstetter/cinder). I also utilize Expo for it's ease of use and vast set of libraries, as well as the simplicity it offers when building and deploying via EAS. React Navigation is used over Expo Router because I find the Expo Router development experience confusing and better suited to web development. React-native-uuid is used for generating UUIDs easily, while Nativewind is used for easy of styling. Axios is used for network requests to the backend.

#### Web
**Language**: Primarily TypeScript, with a smidge of JavaScript
<br/>
**Frameworks/Libraries**:
* React
* Vite
<br/>
**Tools**:
* [Bun](https://bun.com)
<br/>
I've done nothing on this so far - my focus is on the backend and mobile app for now. I'll be fleshing out the web once I have a better feel for the UI from the app and which parts make sense on the web/what specific niches the web code will need to fulfill that the mobile app code can't, won't or shouldn't.
