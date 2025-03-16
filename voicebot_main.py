import streamlit as st
from audiorecorder import audiorecorder
from openai import OpenAI
import os
from datetime import datetime
from gtts import gTTS
import base64
from streamlit_session_browser_storage import SessionStorage


# 기능 구현 함수
def stt(audio, apikey):
    filename = "input.mp3"
    audio.export(filename, format="mp3")
    print(os.path.abspath("input.mp3"))

    with open(filename, "rb") as audio_file:
        client = OpenAI(api_key=apikey)
        response = client.audio.transcriptions.create(model="whisper-1", file=audio_file)

    os.remove(filename)

    return response.text


def ask_gpt(prompt, model, apikey):
    client = OpenAI(api_key=apikey)
    response = client.chat.completions.create(
        model=model,
        messages=prompt
    )
    gpt_response = response.choices[0].message.content
    return gpt_response


def insert_question(question):
    now = datetime.now().strftime("%H:%M")
    st.session_state["chat"] = st.session_state["chat"] + [("user", now, question)]

    st.session_state["messages"] = st.session_state["messages"] + [{"role": "user", "content": question}]


def tts(response):
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)

    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64, {b64}" type="audio/mp3">
            </audio>
        """
        st.markdown(md, unsafe_allow_html=True)

    os.remove(filename)


def clear():
    st.session_state["chat"] = []
    st.session_state["messages"] = [{"role": "system",
                                     "content": "You are a thoughtful assistant. Respond to all input in a fun way and answer in Korean. Never use emojis in your response."}]
    st.session_state["check_reset"] = True
    st.session_state["text_question"] = ""
    st.session_state["current_question"] = ""

# 메인 함수
def main():
    initial_api_key = ""
    audio = None
    print("Main run")
    # print()
    # for k in st.session_state:
    #     print(k, ":", st.session_state[k])
    session_storage = SessionStorage()
    # 기본 설정 시작------------------------------
    st.set_page_config(
        page_title="음성 비서 프로그램",
        layout="wide"
    )

    st.header("음성 비서 프로그램")

    st.markdown("---")

    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write(
            """
            - 음성 비서 프로그램의 UI는 스트림릿을 사용했습니다.
            - STT(Speech-To-Text)는 OpenAI의 Whisper AI를 사용했습니다.
            - 답변은 OpenAI의 GPT 모델을 활용했습니다.
            - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용했습니다.    
            """
        )

    st.markdown("")
    # 기본 설정 끝------------------------------

    # 상태 저장 session_state 시작------------------------------
    if "chat" not in st.session_state:
        st.session_state["chat"] = []
    if "OPENAI_API" not in st.session_state:
        initial_api_key = session_storage.getItem("voicebot_api_key")
        st.session_state["OPENAI_API"] = initial_api_key if initial_api_key is not None else ""
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system",
                                         "content": "You are a thoughtful assistant. Respond to all input in a fun way and answer in Korean. Never use emojis in your response."}]
    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False
    if "current_question" not in st.session_state:
        st.session_state["current_question"] = ""
    # if "audio" not in st.session_state:
    #     st.session_state["audio"] = None
    # 상태 저장 session_state 끝------------------------------

    # 사이드 바 시작------------------------------
    with st.sidebar:
        def update_api_key():
            st.session_state["OPENAI_API"] = st.session_state["api"]
            clear()

        st.session_state["OPENAI_API"] = st.text_input(label="OPENAI API 키",
                                                       placeholder="Enter your API Key",
                                                       value=st.session_state["OPENAI_API"],
                                                       type="password",
                                                       key="api",
                                                       on_change=update_api_key
                                                       )
        if len(st.session_state["OPENAI_API"]) > 0:
            session_storage.setItem("voicebot_api_key", st.session_state["OPENAI_API"])
        else:
            session_storage.deleteItem("voicebot_api_key")

        st.markdown("---")

        model = st.radio(label="GPT 모델", options=["gpt-4o-mini", "gpt-3.5-turbo"], on_change=clear)

        st.markdown("---")

        if st.button(label="초기화"):
            clear()
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role": "system",
                                             "content": "You are a thoughtful assistant. Respond to all input in a fun way and answer in Korean. Never use emojis in your response."}]
            st.session_state["check_reset"] = True
            st.session_state["text_question"] = ""
            # audio = None

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("질문하기")

        # 음성 녹음하기 시작------------------------------
        with st.container(border=True):
            st.write("텍스트로 GPT에게 질문하기")
            with st.form("text_question_input", border=False, clear_on_submit=True):
                question = st.text_input("텍스트로 GPT에게 질문하기", label_visibility="collapsed", autocomplete="off", key="text_question")
                submitted = st.form_submit_button("✏️ 질문하기")

            if submitted:
                if len(question) > 0:
                    insert_question(question)
                    st.session_state["current_question"] = question
                st.session_state["check_reset"] = True

        with st.container(border=True):
            st.write("음성으로 GPT에게 질문하기")
            audio = audiorecorder("🎙️ 질문하기", "❤️ 질문 완료하기", "녹음중...")
            print(audio.duration_seconds, "!!!!!!")
            # st.session_state["audio"] = audio

            if st.session_state["check_reset"]:
                audio = audio.empty()
                st.session_state["check_reset"] = False
            print(audio.duration_seconds, "!!!!!!")
            if audio.duration_seconds > 0:
                st.audio(audio.export().read())

                question = stt(audio, st.session_state["OPENAI_API"])

                insert_question(question)

        # 음성 녹음하기 끝------------------------------

    with col2:
        st.subheader("질문/답변")
        if audio.duration_seconds > 0 or st.session_state["current_question"] != "":
            response = ask_gpt(st.session_state["messages"], model, st.session_state["OPENAI_API"])

            st.session_state["messages"] = st.session_state["messages"] + [{"role": "system", "content": response}]

            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("bot", now, response)]

            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(
                        f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;max-width:450px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                        unsafe_allow_html=True)
                    st.write("")
                else:
                    st.write(
                        f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;color:black;border-radius:12px;padding:8px 12px;margin-right:8px;max-width:450px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                        unsafe_allow_html=True)
                    st.write("")

            tts(response)


    print()
    for k in st.session_state:
        print(k, ":", st.session_state[k])
    # 사이드 바 끝------------------------------


if __name__ == "__main__":
    main()
