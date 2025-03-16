import streamlit as st
from audiorecorder import audiorecorder
from openai import OpenAI
import os
from datetime import datetime
from gtts import gTTS
import base64


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


# 메인 함수
def main():
    print()
    for k in st.session_state:
        print(k, ":", st.session_state[k])

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
        st.session_state["OPENAI_API"] = ""
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system",
                                         "content": "You are a thoughtful assistant. Respond to all input in a fun way and answer in Korean."}]
    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False
    if "current_question" not in st.session_state:
        st.session_state["current_question"] = ""
    # 상태 저장 session_state 끝------------------------------

    # 사이드 바 시작------------------------------
    with st.sidebar:
        st.session_state["OPENAI_API"] = st.text_input(label="OPENAI API 키",
                                                       placeholder="Enter your API Key",
                                                       value=st.session_state["OPENAI_API"],
                                                       type="password")

        st.markdown("---")

        model = st.radio(label="GPT 모델", options=["gpt-4o-mini", "o3-mini"])

        st.markdown("---")

        if st.button(label="초기화"):
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role": "system",
                                             "content": "You are a thoughtful assistant. Respond to all input in a fun way and answer in Korean."}]
            st.session_state["check_reset"] = True

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("질문하기")

        # 음성 녹음하기 시작------------------------------

        with st.form("text_question_input"):
            question = st.text_input("질문을 입력하세요.")
            submitted = st.form_submit_button("GPT에게 질문하기")

        if submitted:
            st.session_state["current_question"] = question
            insert_question(st.session_state["current_question"])

        # st.session_state["current_question"] = st.text_input(label="질문",
        #               placeholder="질문을 입력하세요.",
        #               value=st.session_state["current_question"])
        #
        # if st.button(label="GPT에게 질문하기"):
        #
        #     insert_question(st.session_state["current_question"])

        audio = audiorecorder("클릭하여 녹음하기", "녹음 중...")
        if (audio.duration_seconds > 0) and (st.session_state["check_reset"] is False):
            st.audio(audio.export().read())

            question = stt(audio, st.session_state["OPENAI_API"])

            insert_question(question)

        # 음성 녹음하기 끝------------------------------

    with col2:
        st.subheader("질문/답변")
        if (audio.duration_seconds > 0 or st.session_state["current_question"] != "") and (
                st.session_state["check_reset"] is False):
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

    st.session_state["current_question"] = ""


if __name__ == "__main__":
    main()
