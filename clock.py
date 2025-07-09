import streamlit as st
import time
from datetime import datetime, timedelta
import base64
import io

# Page configuration
st.set_page_config(
    page_title="Study Clock",
    page_icon="⏰",
    layout="centered"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        height: 50px;
        font-size: 20px;
        border-radius: 10px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: scale(1.05);
    }
    div[data-testid="stMetricValue"] {
        font-size: 48px;
    }
    .timer-display {
        padding: 20px;
        border-radius: 15px;
        background-color: #f0f0f0;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'timer_state' not in st.session_state:
    st.session_state.timer_state = 'stopped'  # 'running', 'stopped', 'paused'
    st.session_state.current_phase = 0
    st.session_state.time_remaining = 20 * 60  # Start with 20 minutes
    st.session_state.start_time = None
    st.session_state.completed_sessions = 0
    st.session_state.phases = [
        {'name': 'Study Session', 'duration': 20 * 60, 'color': '#FF6B6B'},
        {'name': 'Short Break', 'duration': 8 * 60, 'color': '#4ECDC4'},
        {'name': 'Final Sprint', 'duration': 2 * 60, 'color': '#45B7D1'}
    ]
    st.session_state.notification_played = False

# Generate a simple beep sound as base64 (since we can't rely on external files)
def generate_beep_sound():
    """Generate a simple beep sound in base64 format"""
    # This is a simple sine wave beep
    import math
    sample_rate = 44100
    duration = 0.5  # seconds
    frequency = 440  # Hz (A4 note)
    
    # Generate sine wave
    samples = []
    for i in range(int(sample_rate * duration)):
        sample = 32767 * math.sin(2 * math.pi * frequency * i / sample_rate)
        samples.append(int(sample))
    
    # Create WAV file in memory
    import wave
    import struct
    
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)   # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', sample))
    
    wav_buffer.seek(0)
    return base64.b64encode(wav_buffer.read()).decode()

def play_notification():
    """Play notification sound using Streamlit's audio component"""
    if not st.session_state.notification_played:
        # Generate beep sound
        beep_sound = generate_beep_sound()
        audio_html = f"""
        <audio autoplay>
            <source src="data:audio/wav;base64,{beep_sound}" type="audio/wav">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
        st.session_state.notification_played = True

def format_time(seconds):
    """Format seconds to MM:SS"""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

def update_timer():
    """Update timer based on elapsed time"""
    if st.session_state.timer_state == 'running':
        elapsed = (datetime.now() - st.session_state.start_time).total_seconds()
        phase_duration = st.session_state.phases[st.session_state.current_phase]['duration']
        time_left = phase_duration - int(elapsed)
        
        if time_left <= 0:
            # Phase completed
            play_notification()
            st.session_state.current_phase += 1
            
            if st.session_state.current_phase >= len(st.session_state.phases):
                # All phases completed
                st.session_state.timer_state = 'stopped'
                st.session_state.current_phase = 0
                st.session_state.completed_sessions += 1
                st.balloons()  # Celebration!
                st.success("🎉 Congratulations! You've completed a full study session!")
            else:
                # Move to next phase
                st.session_state.start_time = datetime.now()
                st.session_state.notification_played = False
                time_left = st.session_state.phases[st.session_state.current_phase]['duration']
        
        return time_left
    else:
        return st.session_state.time_remaining

# Main UI
st.title("🕐 Study Clock")
st.markdown("A Pomodoro-style timer for focused study sessions")
st.markdown("---")

# Display current phase
if st.session_state.timer_state == 'stopped' and st.session_state.current_phase == 0:
    phase_text = "Ready to start"
    phase_color = "#95A5A6"
elif st.session_state.current_phase < len(st.session_state.phases):
    phase_text = st.session_state.phases[st.session_state.current_phase]['name']
    phase_color = st.session_state.phases[st.session_state.current_phase]['color']
else:
    phase_text = "Session Complete! 🎉"
    phase_color = "#27AE60"

st.markdown(f"<h2 style='text-align: center; color: {phase_color};'>{phase_text}</h2>", unsafe_allow_html=True)

# Timer display container
timer_container = st.container()
with timer_container:
    timer_placeholder = st.empty()

# Control buttons
col1, col2, col3 = st.columns(3)

with col1:
    start_disabled = st.session_state.timer_state == 'running' or (st.session_state.current_phase >= len(st.session_state.phases))
    if st.button("▶️ Start", disabled=start_disabled, key="start_btn"):
        st.session_state.timer_state = 'running'
        st.session_state.start_time = datetime.now()
        st.session_state.notification_played = False
        st.rerun()

with col2:
    if st.button("⏸️ Stop", disabled=(st.session_state.timer_state != 'running'), key="stop_btn"):
        st.session_state.timer_state = 'stopped'
        # Calculate and save remaining time
        elapsed = (datetime.now() - st.session_state.start_time).total_seconds()
        phase_duration = st.session_state.phases[st.session_state.current_phase]['duration']
        st.session_state.time_remaining = max(0, phase_duration - int(elapsed))
        st.rerun()

with col3:
    if st.button("🔄 Reset", disabled=(st.session_state.timer_state == 'running'), key="reset_btn"):
        st.session_state.timer_state = 'stopped'
        st.session_state.current_phase = 0
        st.session_state.time_remaining = st.session_state.phases[0]['duration']
        st.session_state.notification_played = False
        st.rerun()

# Display timer
if st.session_state.timer_state == 'running':
    time_left = update_timer()
    timer_color = st.session_state.phases[st.session_state.current_phase]['color'] if st.session_state.current_phase < len(st.session_state.phases) else "#27AE60"
    timer_placeholder.markdown(
        f"<div class='timer-display'><h1 style='text-align: center; color: {timer_color}; font-size: 72px; margin: 0;'>{format_time(time_left)}</h1></div>", 
        unsafe_allow_html=True
    )
else:
    # Display static time when stopped
    if st.session_state.current_phase < len(st.session_state.phases):
        display_time = st.session_state.time_remaining
        timer_color = st.session_state.phases[st.session_state.current_phase]['color']
    else:
        display_time = 0
        timer_color = "#27AE60"
    timer_placeholder.markdown(
        f"<div class='timer-display'><h1 style='text-align: center; color: {timer_color}; font-size: 72px; margin: 0;'>{format_time(display_time)}</h1></div>", 
        unsafe_allow_html=True
    )

# Progress indicator
if st.session_state.current_phase < len(st.session_state.phases):
    phase_duration = st.session_state.phases[st.session_state.current_phase]['duration']
    if st.session_state.timer_state == 'running':
        time_left = update_timer()
        progress = (phase_duration - time_left) / phase_duration
    else:
        progress = (phase_duration - st.session_state.time_remaining) / phase_duration
    
    st.progress(progress)

# Phase information
st.markdown("---")
st.markdown("### Timer Phases:")
for i, phase in enumerate(st.session_state.phases):
    if i < st.session_state.current_phase:
        status = "✅"
        style = "text-decoration: line-through; color: #95A5A6;"
    elif i == st.session_state.current_phase:
        status = "▶️"
        style = f"font-weight: bold; color: {phase['color']};"
    else:
        status = "⏳"
        style = "color: #7F8C8D;"
    
    st.markdown(f"<span style='{style}'>{status} **{phase['name']}**: {phase['duration']//60} minutes</span>", unsafe_allow_html=True)

# Settings section (collapsible)
with st.expander("⚙️ Settings"):
    st.markdown("### Customize Timer Durations")
    st.warning("⚠️ Changing settings will reset the current timer!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        study_duration = st.number_input(
            "Study (min)", 
            min_value=1, 
            max_value=60, 
            value=20,
            key="study_dur"
        )
    
    with col2:
        break_duration = st.number_input(
            "Break (min)", 
            min_value=1, 
            max_value=30, 
            value=8,
            key="break_dur"
        )
    
    with col3:
        final_duration = st.number_input(
            "Sprint (min)", 
            min_value=1, 
            max_value=15, 
            value=2,
            key="final_dur"
        )
    
    if st.button("Apply Settings", key="apply_settings"):
        st.session_state.phases = [
            {'name': 'Study Session', 'duration': study_duration * 60, 'color': '#FF6B6B'},
            {'name': 'Short Break', 'duration': break_duration * 60, 'color': '#4ECDC4'},
            {'name': 'Final Sprint', 'duration': final_duration * 60, 'color': '#45B7D1'}
        ]
        st.session_state.timer_state = 'stopped'
        st.session_state.current_phase = 0
        st.session_state.time_remaining = st.session_state.phases[0]['duration']
        st.success("✅ Settings updated!")
        time.sleep(1)
        st.rerun()

# Sidebar statistics
st.sidebar.markdown("## 📊 Statistics")
st.sidebar.metric("Completed Sessions", st.session_state.completed_sessions)
st.sidebar.metric("Total Study Time", f"{st.session_state.completed_sessions * 30} min")

# Motivational quotes
quotes = [
    "The secret of getting ahead is getting started. - Mark Twain",
    "It does not matter how slowly you go as long as you do not stop. - Confucius",
    "Success is the sum of small efforts repeated day in and day out. - Robert Collier",
    "The only way to do great work is to love what you do. - Steve Jobs",
    "Believe you can and you're halfway there. - Theodore Roosevelt"
]
import random
if st.session_state.timer_state == 'stopped' and st.session_state.current_phase == 0:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💭 Motivation")
    st.sidebar.info(random.choice(quotes))

# Instructions
st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 How to Use")
st.sidebar.markdown("""
1. Click **Start** to begin the timer
2. Complete all three phases:
   - 20 min study session
   - 8 min break
   - 2 min final sprint
3. Timer auto-advances between phases
4. Click **Stop** to pause
5. Click **Reset** to start over
""")

# Auto-refresh for running timer
if st.session_state.timer_state == 'running':
    time.sleep(1)
    st.rerun()