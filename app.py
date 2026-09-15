"""
app.py — StegoSecurity: Private message hiding made simple.

A high-tech cybersecurity steganography terminal interface featuring
AES-256-GCM authenticated encryption and LSB carrier embedding.
"""

import io
import os
import streamlit as st
import numpy as np
from PIL import Image

from crypto_utils import encrypt_message, decrypt_message
from stego import embed_data, extract_data, calculate_capacity as stego_capacity
from analysis import (
    calculate_mse,
    calculate_psnr,
    get_histogram_data,
    get_bit_plane,
    calculate_capacity,
    calculate_pixel_difference_stats,
    get_amplified_difference_image,
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="StegoSecurity — Private Message Hiding Made Simple",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CYBERSECURITY HUD CSS THEME
# ─────────────────────────────────────────────────────────────────────────────

CYBER_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0');

    /* Global Base */
    .stApp {
        background-color: #0f131c !important;
        color: #dfe2ee !important;
        font-family: 'Geist', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #dbfcff !important;
        letter-spacing: -0.02em !important;
        font-weight: 600 !important;
    }
    p, li, span, label {
        color: #dfe2ee;
        font-family: 'Geist', sans-serif;
    }

    /* Code & Monospace */
    code, pre, .mono {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0a0e16 !important;
        border-right: 1px solid #262a33 !important;
        box-shadow: 0 1px 8px rgba(0,0,0,0.5) !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #262a33 !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #b9cacb !important;
        font-family: 'Geist', sans-serif !important;
        font-size: 0.92rem !important;
        padding: 6px 12px !important;
        border-radius: 4px !important;
        transition: all 0.15s ease !important;
    }
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        background-color: #181c24 !important;
        color: #dbfcff !important;
    }

    /* Cyber Containers */
    .cyber-card {
        background-color: #181c24;
        border: 1px solid #262a33;
        border-radius: 6px;
        padding: 1.25rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .cyber-card-inner {
        background-color: #1c2028;
        border: 1px solid #31353e;
        border-radius: 4px;
        padding: 0.85rem;
    }

    /* HUD Header Bar */
    .hud-header {
        background-color: #181c24;
        border: 1px solid #262a33;
        border-radius: 6px;
        padding: 0.65rem 1.25rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 8px rgba(0,0,0,0.4);
    }

    /* Telemetry Badges */
    .badge-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 3px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-weight: 600;
    }
    .badge-cyan {
        background-color: rgba(0, 240, 255, 0.12);
        color: #00f0ff;
        border: 1px solid rgba(0, 240, 255, 0.3);
    }
    .badge-green {
        background-color: rgba(78, 222, 163, 0.12);
        color: #4edea3;
        border: 1px solid rgba(78, 222, 163, 0.3);
    }
    .badge-blue {
        background-color: rgba(123, 208, 255, 0.12);
        color: #7bd0ff;
        border: 1px solid rgba(123, 208, 255, 0.3);
    }
    .badge-dark {
        background-color: #262a33;
        color: #b9cacb;
        border: 1px solid #31353e;
    }

    /* Pulse Dot */
    .pulse-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #4edea3;
        box-shadow: 0 0 8px #4edea3;
        animation: cyberPulse 2s infinite ease-in-out;
    }
    @keyframes cyberPulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.85); }
    }

    /* Action Buttons */
    div.stButton > button:first-child {
        background-color: #00f0ff !important;
        color: #00363a !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        border: 1px solid #00f0ff !important;
        border-radius: 4px !important;
        padding: 0.65rem 1.5rem !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.35) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:first-child:hover {
        background-color: #7df4ff !important;
        color: #002022 !important;
        box-shadow: 0 0 28px rgba(0, 240, 255, 0.6) !important;
        border-color: #7df4ff !important;
    }

    div.stDownloadButton > button:first-child {
        background-color: #00f0ff !important;
        color: #00363a !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        border: 1px solid #00f0ff !important;
        border-radius: 4px !important;
        padding: 0.65rem 1.5rem !important;
        box-shadow: 0 0 24px rgba(0, 240, 255, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    div.stDownloadButton > button:first-child:hover {
        background-color: #7df4ff !important;
        color: #002022 !important;
        box-shadow: 0 0 32px rgba(0, 240, 255, 0.5) !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #0a0e16 !important;
        border: 1px solid #262a33 !important;
        color: #dfe2ee !important;
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 4px !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #00f0ff !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.25) !important;
    }

    /* Metric Cards */
    .telemetry-cell {
        background-color: #1c2028;
        border: 1px solid #262a33;
        border-radius: 4px;
        padding: 0.85rem;
    }
    .telemetry-title {
        font-family: 'Geist', sans-serif;
        font-size: 11px;
        color: #849495;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .telemetry-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.15rem;
        font-weight: 600;
        color: #dbfcff;
        margin-top: 0.25rem;
    }
    .telemetry-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        color: #b9cacb;
        margin-top: 0.2rem;
    }

    /* Tables */
    .hud-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-size: 0.88rem;
    }
    .hud-table th {
        background-color: #1c2028;
        color: #00f0ff;
        text-align: left;
        padding: 0.75rem 1rem;
        border: 1px solid #262a33;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .hud-table td {
        padding: 0.75rem 1rem;
        border: 1px solid #262a33;
        color: #dfe2ee;
    }
    .hud-table tr:nth-child(even) {
        background-color: #181c24;
    }
    .hud-table tr:nth-child(odd) {
        background-color: #0f131c;
    }

    hr {
        border-color: #262a33 !important;
    }
</style>
"""
st.markdown(CYBER_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def image_to_bytes(image: Image.Image) -> bytes:
    """Convert a PIL Image to lossless PNG bytes for download."""
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def load_and_validate_photo(uploaded_file) -> tuple[Image.Image, str, bool]:
    """
    Safely open and validate an uploaded photo using Pillow.
    Normalizes any image format (JPG, PNG, WEBP, etc.) to RGB.
    Returns: (rgb_image, original_format, was_converted)
    """
    raw_img = Image.open(uploaded_file)
    raw_img.load()
    original_format = (raw_img.format or "PNG").upper()
    was_converted = original_format != "PNG"
    rgb_img = raw_img.convert("RGB")
    return rgb_img, original_format, was_converted

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.5rem 0 1rem 0; display: flex; items-center; gap: 0.75rem;">
            <div style="padding: 0.4rem; background-color: #00f0ff; color: #00363a; border-radius: 4px; display: flex; align-items: center; justify-content: center; height: 36px; width: 36px;">
                <span class="material-symbols-outlined" style="font-size: 24px;">shield</span>
            </div>
            <div>
                <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.25rem; font-weight: 700; color: #dbfcff; line-height: 1.1;">StegoSecurity</div>
                <div style="font-size: 11px; color: #849495; margin-top: 2px;">Private message hiding made simple</div>
            </div>
        </div>
        <div style="margin-bottom: 1.25rem; background-color: #181c24; border: 1px solid #262a33; padding: 0.4rem 0.65rem; border-radius: 4px; display: flex; align-items: center; justify-content: space-between;">
            <span class="badge-chip" style="color: #b9cacb; padding: 0;">SEC_NODE // LSB-v2.4</span>
            <span class="pulse-dot"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_selection = st.radio(
        "Navigation",
        [
            "Home",
            "Encrypt & Hide",
            "Extract & Decrypt",
            "Security Analysis",
            "Cryptography vs Steganography",
            "About",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        """
        <div class="cyber-card" style="padding: 0.85rem; margin-top: 2rem;">
            <div style="display: flex; align-items: center; gap: 0.4rem; color: #4edea3; margin-bottom: 0.35rem;">
                <span class="material-symbols-outlined" style="font-size: 16px;">verified_user</span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 600; text-transform: uppercase;">Zero-Leak Architecture</span>
            </div>
            <p style="font-size: 11px; color: #849495; line-height: 1.4; margin: 0 0 0.5rem 0;">
                Local Processing • No external APIs • Zero key retention
            </p>
            <div style="display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #262a33; padding-top: 0.4rem; font-family: 'JetBrains Mono', monospace; font-size: 9px;">
                <span style="color: #849495;">MEMORY_ISOLATED</span>
                <span style="color: #00f0ff;">0x00_PERSIST</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# TOP HUD STATUS BANNER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="hud-header">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span class="pulse-dot"></span>
            <div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #00f0ff; font-weight: 600; letter-spacing: 0.05em;">ENCRYPTION ENGINE READY</div>
                <div style="font-size: 10px; color: #849495;">AES-256-GCM / LSB ENGINE // OWASP-600K-PBKDF2</div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 0.85rem;">
            <span class="badge-chip badge-dark">HOST: LOCAL_SANDBOX</span>
            <span class="badge-chip badge-cyan">DEVICE_ISOLATION: STRICT</span>
            <span class="badge-chip badge-green">EPHEMERAL_SESSION</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: HOME
# ─────────────────────────────────────────────────────────────────────────────

if nav_selection == "Home":
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                <span class="badge-chip badge-cyan">OVERVIEW // SEC_DIRECTIVE</span>
                <span class="badge-chip badge-green">CLIENT_LOCAL</span>
            </div>
            <h1 style="margin: 0; font-size: 2.4rem;">StegoSecurity</h1>
            <p style="color: #00f0ff; font-size: 1.1rem; margin: 0.25rem 0 0.5rem 0;">Hide a private message inside a photo.</p>
            <p style="color: #b9cacb; font-size: 0.95rem; max-width: 800px; line-height: 1.6;">
                Your message is encrypted first using authenticated AES-256-GCM and then hidden within image pixels using LSB steganography. Everything is processed locally in RAM with zero network leakage.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Workflow Graphic
    st.markdown(
        """
        <div class="cyber-card" style="text-align: center; padding: 1.5rem 1rem;">
            <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
                <div class="badge-chip badge-dark" style="padding: 0.6rem 1.2rem; font-size: 13px;">Your Message</div>
                <span style="color: #00f0ff; font-size: 1.2rem; font-weight: bold;">→</span>
                <div class="badge-chip badge-cyan" style="padding: 0.6rem 1.2rem; font-size: 13px;">AES-256-GCM Encrypt</div>
                <span style="color: #00f0ff; font-size: 1.2rem; font-weight: bold;">→</span>
                <div class="badge-chip badge-green" style="padding: 0.6rem 1.2rem; font-size: 13px;">LSB Hide in Photo</div>
                <span style="color: #00f0ff; font-size: 1.2rem; font-weight: bold;">→</span>
                <div class="badge-chip badge-blue" style="padding: 0.6rem 1.2rem; font-size: 13px;">Share Protected Carrier</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br/>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="cyber-card">
                <div style="display: flex; align-items: center; gap: 0.5rem; color: #00f0ff; margin-bottom: 0.5rem;">
                    <span class="material-symbols-outlined">lock</span>
                    <h4 style="margin: 0; color: #dbfcff;">Encrypted</h4>
                </div>
                <p style="color: #b9cacb; font-size: 0.9rem; margin: 0; line-height: 1.6;">
                    Messages are locked with authenticated AES-256 encryption before being embedded inside the photo pixels.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="cyber-card">
                <div style="display: flex; align-items: center; gap: 0.5rem; color: #4edea3; margin-bottom: 0.5rem;">
                    <span class="material-symbols-outlined">visibility_off</span>
                    <h4 style="margin: 0; color: #dbfcff;">Hidden</h4>
                </div>
                <p style="color: #b9cacb; font-size: 0.9rem; margin: 0; line-height: 1.6;">
                    Data is woven invisibly into the pixel color channels. The final photo looks completely normal to human observers.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="cyber-card">
                <div style="display: flex; align-items: center; gap: 0.5rem; color: #7bd0ff; margin-bottom: 0.5rem;">
                    <span class="material-symbols-outlined">memory</span>
                    <h4 style="margin: 0; color: #dbfcff;">Processed Locally</h4>
                </div>
                <p style="color: #b9cacb; font-size: 0.9rem; margin: 0; line-height: 1.6;">
                    All key derivation, encryption, and spatial embedding run 100% on your device with no external API calls.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: ENCRYPT & HIDE (BENTO WORKFLOW)
# ─────────────────────────────────────────────────────────────────────────────

elif nav_selection == "Encrypt & Hide":
    # Header Banner
    st.markdown(
        """
        <div style="display: flex; flex-direction: column; gap: 0.35rem; margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span class="badge-chip badge-cyan">WORKSPACE // ENCRYPTION_NODE_01</span>
                <span class="badge-chip badge-green">ACTIVE_THREAD</span>
            </div>
            <h1 style="margin: 0.2rem 0; font-size: 2.2rem;">Encrypt & Hide</h1>
            <p style="color: #b9cacb; font-size: 0.95rem; margin: 0; max-width: 850px; line-height: 1.6;">
                Embed an AES-256-GCM encrypted payload invisibly within ordinary image pixels using RGB Least Significant Bit (LSB) steganography.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Bento 3-column Layout
    col_step1, col_step2, col_step3 = st.columns(3)

    # ── STEP 1 ──
    with col_step1:
        st.markdown(
            """
            <div class="cyber-card" style="height: 100%;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.4rem;">
                        <span class="badge-chip badge-dark">01</span>
                        <span style="font-weight: 600; color: #dbfcff;">Choose a Photo</span>
                    </div>
                    <span class="badge-chip badge-green">CARRIER_NODE</span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "Upload photo",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
            help="Upload any normal photo. JPG, JPEG, and PNG are supported.",
            key="encrypt_uploader",
            label_visibility="collapsed",
        )

        cover_image = None
        was_converted = False
        original_format = ""

        if uploaded_file:
            try:
                cover_image, original_format, was_converted = load_and_validate_photo(uploaded_file)
                st.image(cover_image, caption="Carrier Preview", width="stretch")
                w, h = cover_image.size
                cap = calculate_capacity(cover_image)
                cap_kb = cap["max_bytes"] / 1024

                st.markdown(
                    f"""
                    <div class="cyber-card-inner" style="margin-top: 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span style="color: #849495;">DIMENSIONS:</span>
                            <span style="color: #dfe2ee;">{w} × {h} px</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span style="color: #849495;">PLANE MODE:</span>
                            <span style="color: #dfe2ee;">RGB 24-bit Lossless</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #849495;">MAX CAPACITY:</span>
                            <span style="color: #00f0ff;">{cap_kb:.1f} KB</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            except Exception:
                st.error("Please choose a valid photo.")
                cover_image = None

        st.markdown("</div>", unsafe_allow_html=True)

    # ── STEP 2 ──
    with col_step2:
        st.markdown(
            """
            <div class="cyber-card" style="height: 100%;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.4rem;">
                        <span class="badge-chip badge-cyan" style="color: #00363a; background: #00f0ff;">02</span>
                        <span style="font-weight: 600; color: #dbfcff;">Your Secret Message</span>
                    </div>
                    <span class="badge-chip badge-blue">RAW_TEXT</span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        secret_message = st.text_area(
            "Payload",
            placeholder="Type or paste the secret message you want to hide...",
            height=145,
            key="secret_msg_box",
            label_visibility="collapsed",
        )

        msg_len = len(secret_message)
        st.markdown(
            f"""
            <div class="cyber-card-inner" style="margin-top: 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span style="color: #849495;">CHARACTER COUNT:</span>
                    <span style="color: #00f0ff;">{msg_len} characters</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span style="color: #849495;">CIPHERTEXT + AUTH OVERHEAD:</span>
                    <span style="color: #4edea3;">+44 Bytes</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #849495;">ESTIMATED FOOTPRINT:</span>
                    <span style="color: #7bd0ff;">{(msg_len + 44) * 8} LSB bits</span>
                </div>
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── STEP 3 ──
    with col_step3:
        st.markdown(
            """
            <div class="cyber-card" style="height: 100%;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.4rem;">
                        <span class="badge-chip badge-dark">03</span>
                        <span style="font-weight: 600; color: #dbfcff;">Set Security Password</span>
                    </div>
                    <span class="badge-chip badge-green">KDF_READY</span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        password = st.text_input(
            "Passphrase",
            type="password",
            placeholder="Enter secure password",
            key="pwd_box",
            label_visibility="collapsed",
        )
        confirm_password = st.text_input(
            "Confirm Passphrase",
            type="password",
            placeholder="Confirm secure password",
            key="pwd_confirm_box",
            label_visibility="collapsed",
        )

        st.markdown(
            """
            <div class="cyber-card-inner" style="margin-top: 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span style="color: #849495;">KDF SPEC:</span>
                    <span style="color: #4edea3;">PBKDF2-HMAC-SHA256</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span style="color: #849495;">ITERATIONS:</span>
                    <span style="color: #dfe2ee;">600,000 Rounds</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #849495;">NONCE:</span>
                    <span style="color: #00f0ff;">96-bit Random GCM IV</span>
                </div>
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── PRIMARY ACTION BAR ──
    st.markdown(
        """
        <div class="cyber-card" style="display: flex; align-items: center; justify-content: space-between; padding: 1rem 1.5rem; margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span class="material-symbols-outlined" style="color: #00f0ff; font-size: 28px;">key</span>
                <div>
                    <div style="font-weight: 600; color: #dbfcff; font-size: 1rem;">Dual-Layer Security Operation</div>
                    <div style="font-size: 12px; color: #849495;">Authenticated encryption followed by deterministic spatial bit interleaving</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    encrypt_clicked = st.button("ENCRYPT & HIDE PAYLOAD", width="stretch")

    if encrypt_clicked:
        validation_errors = []
        if not cover_image:
            validation_errors.append("Please choose a valid photo.")
        if not secret_message:
            validation_errors.append("Please enter the secret message you want to hide.")
        if not password:
            validation_errors.append("Please enter a security password.")
        elif len(password) < 8:
            validation_errors.append("Password must be at least 8 characters.")
        if password and confirm_password and password != confirm_password:
            validation_errors.append("Passwords do not match.")
        elif password and not confirm_password:
            validation_errors.append("Please confirm your password.")

        if validation_errors:
            for err in validation_errors:
                st.error(err)
        else:
            try:
                # 1. Encrypt with AES-256-GCM
                encrypted_payload = encrypt_message(secret_message, password)
                max_bytes = stego_capacity(cover_image)

                if len(encrypted_payload) > max_bytes:
                    st.error("This photo cannot hold this message. Please choose a larger photo or use a shorter message.")
                else:
                    # 2. Embed into RGB LSBs
                    stego_img = embed_data(cover_image, encrypted_payload)

                    # 3. Serialize to lossless PNG bytes
                    stego_png_bytes = image_to_bytes(stego_img)

                    # 4. Reload from PNG bytes for memory isolation
                    stego_img_reloaded = Image.open(io.BytesIO(stego_png_bytes))
                    stego_img_reloaded.load()

                    # 5. Immediate verification
                    extracted_payload = extract_data(stego_img_reloaded)
                    verified_message = decrypt_message(extracted_payload, password)

                    if verified_message != secret_message:
                        st.error("Embedding verification failed: the hidden data could not be recovered accurately.")
                    else:
                        diff_stats = calculate_pixel_difference_stats(cover_image, stego_img_reloaded)
                        mse_val = calculate_mse(cover_image, stego_img_reloaded)
                        psnr_val = calculate_psnr(mse_val)
                        amplified_img = get_amplified_difference_image(cover_image, stego_img_reloaded, scale=255)

                        st.session_state["active_stego_bytes"] = stego_png_bytes
                        st.session_state["active_stego_img"] = stego_img_reloaded
                        st.session_state["active_cover_img"] = cover_image
                        st.session_state["active_amplified_img"] = amplified_img
                        st.session_state["active_dimensions"] = f"{cover_image.width} × {cover_image.height}"
                        st.session_state["active_payload_bytes"] = len(encrypted_payload)
                        st.session_state["active_capacity_bytes"] = max_bytes
                        st.session_state["active_mse"] = mse_val
                        st.session_state["active_psnr"] = psnr_val
                        st.session_state["active_diff_stats"] = diff_stats
                        st.session_state["active_converted"] = was_converted
                        st.session_state["hide_success"] = True

            except Exception:
                st.error("An error occurred during cryptographic processing. Please try again.")

    # ── SUCCESS & RESULTS SECTION ──
    if st.session_state.get("hide_success") and "active_stego_img" in st.session_state:
        st.markdown("---")
        st.markdown(
            """
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                <div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span class="pulse-dot"></span>
                        <h2 style="margin: 0; font-size: 1.6rem; color: #dbfcff;">Your message is hidden.</h2>
                    </div>
                    <p style="color: #849495; font-size: 0.9rem; margin: 0.2rem 0 0 0;">
                        The image looks visually identical, but now encapsulates the authenticated ciphertext.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Dual Viewport Cards
        col_res_l, col_res_r = st.columns(2)
        with col_res_l:
            st.markdown(
                """
                <div class="cyber-card" style="padding: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                        <span style="color: #849495;">INPUT_CARRIER: Original Photo</span>
                        <span class="badge-chip badge-dark">Standard RGB</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            st.image(st.session_state["active_cover_img"], caption="Original Cover Photo", width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_res_r:
            st.markdown(
                """
                <div class="cyber-card" style="padding: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                        <span style="color: #4edea3;">LSB_ENCODED: Protected Photo (.png)</span>
                        <span class="badge-chip badge-green">Looks Identical</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            st.image(st.session_state["active_stego_img"], caption="Protected Stego Photo", width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)

        # Three Verification Cards
        st.markdown(
            """
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1.25rem 0;">
                <div class="cyber-card" style="display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem;">
                    <span class="material-symbols-outlined" style="color: #4edea3; font-size: 24px;">check_circle</span>
                    <div>
                        <div style="font-weight: 600; color: #dbfcff; font-size: 13px;">Message Encrypted</div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #849495;">AES-256-GCM / 12-byte Nonce</div>
                    </div>
                </div>
                <div class="cyber-card" style="display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem;">
                    <span class="material-symbols-outlined" style="color: #4edea3; font-size: 24px;">check_circle</span>
                    <div>
                        <div style="font-weight: 600; color: #dbfcff; font-size: 13px;">Message Hidden</div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #849495;">RGB LSB Steganography</div>
                    </div>
                </div>
                <div class="cyber-card" style="display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem;">
                    <span class="material-symbols-outlined" style="color: #4edea3; font-size: 24px;">check_circle</span>
                    <div>
                        <div style="font-weight: 600; color: #dbfcff; font-size: 13px;">Protected Image Ready</div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #849495;">PNG / Lossless Compression</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Telemetry & Steganalytic Metrics Panel
        st.markdown(
            """
            <div class="cyber-card" style="margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span class="material-symbols-outlined" style="color: #00f0ff;">analytics</span>
                        <h3 style="margin: 0; font-size: 1.15rem; color: #dbfcff;">IMAGE TELEMETRY & STEGANALYTIC METRICS</h3>
                    </div>
                    <span class="badge-chip badge-green">MATH_VERIFIED: IEEE_754</span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        payload_b = st.session_state["active_payload_bytes"]
        payload_str = f"{payload_b / 1024:.2f} KB ({payload_b} bytes)" if payload_b >= 1024 else f"{payload_b} bytes"

        cap_b = st.session_state["active_capacity_bytes"]
        cap_str = f"{cap_b / 1024:.2f} KB ({cap_b:,} bytes)" if cap_b >= 1024 else f"{cap_b} bytes"

        cap_pct = (payload_b / cap_b * 100) if cap_b > 0 else 0.0

        mse_val = st.session_state["active_mse"]
        psnr_val = st.session_state["active_psnr"]
        psnr_str = f"{psnr_val:.2f} dB" if psnr_val != float("inf") else "∞ dB"

        diff_stats = st.session_state["active_diff_stats"]
        pct_changed = diff_stats["pct_channels_changed"]

        tm1, tm2, tm3, tm4 = st.columns(4)
        with tm1:
            st.markdown(
                f"""
                <div class="telemetry-cell">
                    <div class="telemetry-title">Dimensions</div>
                    <div class="telemetry-value">{st.session_state['active_dimensions']}</div>
                    <div class="telemetry-sub">{diff_stats['total_pixels']:,} pixels</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with tm2:
            st.markdown(
                f"""
                <div class="telemetry-cell">
                    <div class="telemetry-title">Payload Size</div>
                    <div class="telemetry-value" style="color: #00f0ff;">{payload_str}</div>
                    <div class="telemetry-sub">AES-GCM Auth Encrypted</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with tm3:
            st.markdown(
                f"""
                <div class="telemetry-cell">
                    <div class="telemetry-title">Total Capacity</div>
                    <div class="telemetry-value">{cap_str}</div>
                    <div class="telemetry-sub">Utilization: {cap_pct:.3f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with tm4:
            st.markdown(
                f"""
                <div class="telemetry-cell">
                    <div class="telemetry-title">Changed Pixels</div>
                    <div class="telemetry-value" style="color: #7bd0ff;">{pct_changed:.2f}%</div>
                    <div class="telemetry-sub">{diff_stats['changed_channels']:,} channel values</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        tm5, tm6, tm7, tm8 = st.columns(4)
        with tm5:
            st.markdown(
                f"""
                <div class="telemetry-cell">
                    <div class="telemetry-title">MSE (Mean Squared Error)</div>
                    <div class="telemetry-value" style="color: #4edea3;">{mse_val:.6f}</div>
                    <div class="telemetry-sub">Near-zero imperceptible shift</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with tm6:
            st.markdown(
                f"""
                <div class="telemetry-cell">
                    <div class="telemetry-title">PSNR (Fidelity)</div>
                    <div class="telemetry-value" style="color: #00f0ff;">{psnr_str}</div>
                    <div class="telemetry-sub">Threshold > 40 dB is invisible</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with tm7:
            st.markdown(
                f"""
                <div class="telemetry-cell">
                    <div class="telemetry-title">Integrity Tag (GCM MAC)</div>
                    <div class="telemetry-value" style="color: #7bd0ff;">VALID (128-bit)</div>
                    <div class="telemetry-sub">Tamper-evident verification</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with tm8:
            st.markdown(
                f"""
                <div class="telemetry-cell">
                    <div class="telemetry-title">Security Model</div>
                    <div class="telemetry-value" style="color: #4edea3;">DEFENSE IN DEPTH</div>
                    <div class="telemetry-sub">Crypto + Stego Stacked</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # Amplified Difference View
        if "show_amplified" not in st.session_state:
            st.session_state["show_amplified"] = False

        btn_txt = "HIDE DIFFERENCE HEATMAP" if st.session_state["show_amplified"] else "VIEW AMPLIFIED DIFFERENCE"
        if st.button(btn_txt, width="stretch", key="btn_toggle_amplified_hud"):
            st.session_state["show_amplified"] = not st.session_state["show_amplified"]
            st.rerun()

        if st.session_state.get("show_amplified"):
            st.markdown(
                """
                <div class="cyber-card" style="margin-top: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span class="badge-chip badge-cyan">DIFF_AMPLIFIED × 255</span>
                        <span style="font-size: 11px; color: #849495;">Changes are exaggerated for visualization</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            st.image(
                st.session_state["active_amplified_img"],
                caption="Delta Heatmap (Every modified LSB pixel scaled to full 255 brightness)",
                width="stretch",
            )
            st.markdown("</div>", unsafe_allow_html=True)

        # Download Dispatch Box
        st.markdown(
            """
            <div class="cyber-card" style="margin-top: 1.5rem; margin-bottom: 1rem;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #00f0ff; text-transform: uppercase; margin-bottom: 0.25rem;">
                    SECURE_ARTIFACT_DISPATCH
                </div>
                <h3 style="margin: 0; color: #dbfcff; font-size: 1.25rem;">Export Protected Carrier</h3>
                <p style="color: #b9cacb; font-size: 0.9rem; margin: 0.35rem 0 1rem 0; line-height: 1.5;">
                    Always distribute this file in lossless PNG format. Lossy compression engines (such as JPEG re-encoding, social media messengers, or WebP transcoders) will overwrite the least significant bits and destroy the ciphertext.
                </p>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            label="DOWNLOAD PROTECTED PHOTO (.PNG)",
            data=st.session_state["active_stego_bytes"],
            file_name="stegosecurity_protected_carrier.png",
            mime="image/png",
            width="stretch",
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: EXTRACT & DECRYPT
# ─────────────────────────────────────────────────────────────────────────────

elif nav_selection == "Extract & Decrypt":
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span class="badge-chip badge-cyan">RECEIVER_NODE // DECRYPTION_02</span>
                <span class="badge-chip badge-green">INSPECTION_MODE</span>
            </div>
            <h1 style="margin: 0.2rem 0; font-size: 2.2rem;">Extract & Decrypt</h1>
            <p style="color: #b9cacb; font-size: 0.95rem; margin: 0; max-width: 850px; line-height: 1.6;">
                Upload a protected PNG carrier, extract the embedded LSB byte stream, and verify the AES-256-GCM authentication tag using your passphrase.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_dec1, col_dec2 = st.columns(2)

    with col_dec1:
        st.markdown(
            """
            <div class="cyber-card" style="height: 100%;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.4rem;">
                        <span class="badge-chip badge-dark">01</span>
                        <span style="font-weight: 600; color: #dbfcff;">Choose Protected Photo</span>
                    </div>
                    <span class="badge-chip badge-green">PNG_REQUIRED</span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        stego_upload = st.file_uploader(
            "Upload protected carrier",
            type=["png"],
            help="Upload the protected PNG photo.",
            label_visibility="collapsed",
            key="extract_uploader",
        )

        if stego_upload:
            try:
                preview_stego = Image.open(stego_upload)
                preview_stego.load()
                st.image(preview_stego, caption="Protected Carrier Preview", width="stretch")
            except Exception:
                st.error("Please choose a valid photo.")
                stego_upload = None

        st.markdown("</div>", unsafe_allow_html=True)

    with col_dec2:
        st.markdown(
            """
            <div class="cyber-card" style="height: 100%;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.4rem;">
                        <span class="badge-chip badge-dark">02</span>
                        <span style="font-weight: 600; color: #dbfcff;">Enter Security Password</span>
                    </div>
                    <span class="badge-chip badge-blue">PBKDF2_AUTH</span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        decrypt_pwd = st.text_input(
            "Password",
            type="password",
            placeholder="Enter security password used during encryption",
            label_visibility="collapsed",
            key="decrypt_pwd_input",
        )

        st.markdown(
            """
            <div class="cyber-card-inner" style="margin-top: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                <div style="color: #849495; margin-bottom: 0.35rem;">RECOVERY PROTOCOL:</div>
                <div style="color: #dfe2ee; line-height: 1.5;">
                    1. Scan RGB LSBs for 4-byte signature ('STEG')<br/>
                    2. Read 32-bit big-endian payload length header<br/>
                    3. Derive key via 600,000 PBKDF2 rounds using stored salt<br/>
                    4. Authenticate 128-bit GCM tag before deciphering
                </div>
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    recover_clicked = st.button("EXTRACT & DECRYPT PAYLOAD", width="stretch")

    if recover_clicked:
        if not stego_upload:
            st.error("Please choose a valid photo.")
        elif not decrypt_pwd:
            st.error("Please enter your password.")
        else:
            try:
                stego_image_obj = Image.open(stego_upload)
                extracted_data = extract_data(stego_image_obj)
                decrypted_text = decrypt_message(extracted_data, decrypt_pwd)

                st.markdown("---")
                st.markdown(
                    """
                    <div class="cyber-card" style="margin-bottom: 1rem;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span class="pulse-dot"></span>
                                <span style="font-family: 'Space Grotesk', sans-serif; font-size: 1.25rem; font-weight: 700; color: #4edea3;">
                                    MESSAGE RECOVERED & AUTHENTICATED
                                </span>
                            </div>
                            <span class="badge-chip badge-green">GCM_TAG_VERIFIED</span>
                        </div>
                        <p style="font-size: 11px; font-family: 'JetBrains Mono', monospace; color: #849495; margin: 0 0 0.75rem 0;">
                            AUTHENTICATED CIPHERTEXT RECOVERED: ZERO BIT CORRUPTION DETECTED
                        </p>
                    """,
                    unsafe_allow_html=True,
                )
                st.text_area(
                    "Your hidden message",
                    value=decrypted_text,
                    height=140,
                    disabled=True,
                    label_visibility="collapsed",
                )
                st.markdown("</div>", unsafe_allow_html=True)

            except ValueError as ve:
                err_msg = str(ve)
                if "No hidden data" in err_msg or "magic" in err_msg.lower() or "too small" in err_msg.lower():
                    st.error("No hidden message was found in this photo.")
                elif "Decryption failed" in err_msg or "Wrong password" in err_msg:
                    st.error("Unable to recover the message. Check the password.")
                else:
                    st.error("Unable to recover the message. Check the password or make sure this is a protected photo.")
            except Exception:
                st.error("Unable to recover the message. Check the password or make sure this is a protected photo.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4: SECURITY ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

elif nav_selection == "Security Analysis":
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span class="badge-chip badge-cyan">TELEMETRY // DEEP_ANALYSIS</span>
                <span class="badge-chip badge-blue">ACADEMIC_VIVA</span>
            </div>
            <h1 style="margin: 0.2rem 0; font-size: 2.2rem;">Security Analysis</h1>
            <p style="color: #b9cacb; font-size: 0.95rem; margin: 0; max-width: 850px; line-height: 1.6;">
                Formal cryptanalytic and steganographic evaluations demonstrating defense-in-depth principles.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="cyber-card" style="margin-bottom: 1.25rem;">
            <p style="margin: 0; color: #dbfcff; font-size: 1rem; line-height: 1.6;">
                <strong>Core Philosophy:</strong><br/>
                • <em>Encryption protects the message content.</em><br/>
                • <em>Steganography hides the presence of the encrypted message.</em><br/>
                • <em>Combining both provides defense in depth.</em>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    an_col1, an_col2 = st.columns(2)
    with an_col1:
        st.markdown(
            """
            <div class="cyber-card" style="height: 100%;">
                <h4 style="color: #00f0ff; margin-top: 0;">AES-256-GCM</h4>
                <p style="color: #b9cacb; font-size: 0.88rem; line-height: 1.6;">
                    Galois/Counter Mode (GCM) combines counter-mode confidentiality with polynomial universal hashing authentication (GHASH). It produces a 16-byte cryptographic MAC that detects any tampering or bit-flipping immediately.
                </p>
                <div class="cyber-card-inner" style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #dfe2ee;">
                    KEY: 256 bits | NONCE: 96 bits | TAG: 128 bits (GCM)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with an_col2:
        st.markdown(
            """
            <div class="cyber-card" style="height: 100%;">
                <h4 style="color: #00f0ff; margin-top: 0;">PBKDF2-HMAC-SHA256</h4>
                <p style="color: #b9cacb; font-size: 0.88rem; line-height: 1.6;">
                    Converts user passphrases into 256-bit symmetric keys using 600,000 iterations of HMAC-SHA256 and a 16-byte random salt. Meets modern NIST SP 800-132 and OWASP standards against GPU-accelerated dictionary attacks.
                </p>
                <div class="cyber-card-inner" style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #dfe2ee;">
                    ROUNDS: 600,000 | SALT: 128-bit CSPRNG | OUTPUT: 32 Bytes
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    an_col3, an_col4 = st.columns(2)
    with an_col3:
        st.markdown(
            """
            <div class="cyber-card" style="height: 100%;">
                <h4 style="color: #4edea3; margin-top: 0;">LSB Steganography</h4>
                <p style="color: #b9cacb; font-size: 0.88rem; line-height: 1.6;">
                    Modifies the lowest bit of 8-bit RGB color channels, shifting intensity by at most ±1. This is far below the just-noticeable difference (JND) threshold of human visual perception.
                </p>
                <div class="cyber-card-inner" style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #dfe2ee;">
                    HEADER: 4B MAGIC ('STEG') + 4B Length | RGB Only (No Alpha)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with an_col4:
        st.markdown(
            """
            <div class="cyber-card" style="height: 100%;">
                <h4 style="color: #4edea3; margin-top: 0;">MSE & PSNR Metrics</h4>
                <p style="color: #b9cacb; font-size: 0.88rem; line-height: 1.6;">
                    MSE quantifies average squared pixel deviation. PSNR calculates peak signal-to-noise ratio in dB. LSB steganography typically yields PSNR values > 60-70 dB, representing exceptional visual fidelity.
                </p>
                <div class="cyber-card-inner" style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #dfe2ee;">
                    PSNR = 10 * log10(255² / MSE) dB | TARGET: > 40 dB
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    # Interactive Quality Metric Calculator
    with st.expander("INTERACTIVE QUALITY METRIC CALCULATOR"):
        st.markdown("<p style='font-size: 0.85rem; color: #849495;'>Upload an original photo and a protected photo to compute live MSE and PSNR metrics.</p>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            test_orig = st.file_uploader("Original Photo", type=["jpg", "jpeg", "png", "webp"], key="calc_orig")
        with col_c2:
            test_steg = st.file_uploader("Protected Photo", type=["png"], key="calc_steg")

        if test_orig and test_steg:
            try:
                img_1 = Image.open(test_orig).convert("RGB")
                img_2 = Image.open(test_steg).convert("RGB")
                calc_m = calculate_mse(img_1, img_2)
                calc_p = calculate_psnr(calc_m)
                calc_diff = calculate_pixel_difference_stats(img_1, img_2)

                cm1, cm2, cm3 = st.columns(3)
                with cm1:
                    st.metric("MSE", f"{calc_m:.6f}")
                with cm2:
                    psnr_txt = f"{calc_p:.2f} dB" if calc_p != float("inf") else "∞ dB"
                    st.metric("PSNR", psnr_txt)
                with cm3:
                    st.metric("Changed Pixels", f"{calc_diff['pct_channels_changed']:.2f}%")
            except Exception:
                st.error("Error computing metrics for uploaded photos.")

    # Bit-Plane & Histogram Inspector
    with st.expander("BIT-PLANE & HISTOGRAM INSPECTION"):
        inspect_file = st.file_uploader("Upload photo to inspect", type=["jpg", "jpeg", "png", "webp"], key="inspect_uploader")
        if inspect_file:
            try:
                insp_img = Image.open(inspect_file).convert("RGB")
                bp_col1, bp_col2 = st.columns(2)
                with bp_col1:
                    lsb_plane = get_bit_plane(insp_img, bit_position=0)
                    st.image(lsb_plane, caption="Bit Plane 0 (LSB — where stego payload resides)", width="stretch")
                with bp_col2:
                    msb_plane = get_bit_plane(insp_img, bit_position=7)
                    st.image(msb_plane, caption="Bit Plane 7 (MSB — main visual structure)", width="stretch")

                st.markdown("<p style='font-size: 0.85rem; color: #849495; margin-top: 1rem;'>Channel Intensity Histograms</p>", unsafe_allow_html=True)
                hist_data = get_histogram_data(insp_img)
                st.line_chart(
                    {"Red": hist_data["Red"], "Green": hist_data["Green"], "Blue": hist_data["Blue"]},
                    height=200,
                    width="stretch",
                )
            except Exception:
                st.error("Unable to inspect photo.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 5: CRYPTOGRAPHY VS STEGANOGRAPHY
# ─────────────────────────────────────────────────────────────────────────────

elif nav_selection == "Cryptography vs Steganography":
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span class="badge-chip badge-cyan">THEORY // COMPARATIVE_ANALYSIS</span>
                <span class="badge-chip badge-green">DEFENSE_IN_DEPTH</span>
            </div>
            <h1 style="margin: 0.2rem 0; font-size: 2.2rem;">Cryptography vs Steganography</h1>
            <p style="color: #b9cacb; font-size: 0.95rem; margin: 0; max-width: 850px; line-height: 1.6;">
                Comparing confidentiality through encryption versus concealment through steganography.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        st.markdown(
            """
            <div class="cyber-card" style="text-align: center;">
                <h4 style="color: #00f0ff; margin-top: 0;">CRYPTOGRAPHY</h4>
                <div class="badge-chip badge-dark" style="margin: 0.35rem 0;">Message</div>
                <div style="color: #849495; font-weight: bold; margin: 0.25rem 0;">↓</div>
                <div class="badge-chip badge-cyan" style="margin: 0.35rem 0;">Encryption</div>
                <div style="color: #849495; font-weight: bold; margin: 0.25rem 0;">↓</div>
                <div class="badge-chip badge-dark" style="margin: 0.35rem 0;">Unreadable Data</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_w2:
        st.markdown(
            """
            <div class="cyber-card" style="text-align: center;">
                <h4 style="color: #4edea3; margin-top: 0;">STEGANOGRAPHY</h4>
                <div class="badge-chip badge-dark" style="margin: 0.35rem 0;">Message</div>
                <div style="color: #849495; font-weight: bold; margin: 0.25rem 0;">↓</div>
                <div class="badge-chip badge-green" style="margin: 0.35rem 0;">Hidden inside image</div>
                <div style="color: #849495; font-weight: bold; margin: 0.25rem 0;">↓</div>
                <div class="badge-chip badge-dark" style="margin: 0.35rem 0;">Normal-looking photo</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_w3:
        st.markdown(
            """
            <div class="cyber-card" style="text-align: center;">
                <h4 style="color: #7bd0ff; margin-top: 0;">COMBINED APPROACH</h4>
                <div class="badge-chip badge-dark" style="margin: 0.25rem 0;">Message</div>
                <div style="color: #849495; font-weight: bold; margin: 0.15rem 0;">↓</div>
                <div class="badge-chip badge-cyan" style="margin: 0.25rem 0;">AES-256-GCM</div>
                <div style="color: #849495; font-weight: bold; margin: 0.15rem 0;">↓</div>
                <div class="badge-chip badge-green" style="margin: 0.25rem 0;">LSB Stego</div>
                <div style="color: #849495; font-weight: bold; margin: 0.15rem 0;">↓</div>
                <div class="badge-chip badge-blue" style="margin: 0.25rem 0;">Protected Photo</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown(
        """
        <table class="hud-table">
            <thead>
                <tr>
                    <th>Aspect</th>
                    <th>Cryptography</th>
                    <th>Steganography</th>
                    <th>Combined Approach</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Purpose</strong></td>
                    <td>Protect data content</td>
                    <td>Conceal communication presence</td>
                    <td>Provide defense in depth</td>
                </tr>
                <tr>
                    <td><strong>Main goal</strong></td>
                    <td>Make data unreadable</td>
                    <td>Hide the existence of the message</td>
                    <td>Hide existence and keep content unreadable</td>
                </tr>
                <tr>
                    <td><strong>What is protected?</strong></td>
                    <td>Message content & integrity</td>
                    <td>Presence of communication</td>
                    <td>Both content and existence</td>
                </tr>
                <tr>
                    <td><strong>Visibility</strong></td>
                    <td>Obvious ciphertext</td>
                    <td>Normal-looking photo</td>
                    <td>Normal-looking photo</td>
                </tr>
                <tr>
                    <td><strong>Detectability</strong></td>
                    <td>Easily identified as encrypted</td>
                    <td>Invisible to human eye; detectable via steganalysis</td>
                    <td>If detected, reveals only encrypted data</td>
                </tr>
                <tr>
                    <td><strong>Main limitation</strong></td>
                    <td>Does not conceal existence</td>
                    <td>Fragile to modifications</td>
                    <td>Requires lossless PNG output</td>
                </tr>
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 6: ABOUT
# ─────────────────────────────────────────────────────────────────────────────

elif nav_selection == "About":
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span class="badge-chip badge-cyan">METADATA // PROJECT_SPECS</span>
                <span class="badge-chip badge-green">COLLEGE_CYBERSECURITY</span>
            </div>
            <h1 style="margin: 0.2rem 0; font-size: 2.2rem;">StegoSecurity</h1>
            <p style="color: #00f0ff; font-size: 1.05rem; margin: 0.25rem 0 0.5rem 0;">Private message hiding made simple.</p>
            <p style="color: #b9cacb; font-size: 0.95rem; margin: 0;">Encrypt a message and hide it inside an ordinary photo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="cyber-card" style="margin-bottom: 1.5rem;">
            <p style="margin: 0; color: #849495; font-size: 0.8rem; text-transform: uppercase;">PROJECT TITLE</p>
            <p style="margin: 0.2rem 0 0.75rem 0; font-size: 1.15rem; color: #dbfcff; font-weight: 600;">
                Steganography vs Cryptography — Compare & Implement
            </p>
            <p style="margin: 0; color: #849495; font-size: 0.8rem; text-transform: uppercase;">DESIGNATION</p>
            <p style="margin: 0.2rem 0 0 0; color: #dfe2ee; font-size: 0.95rem;">
                Educational cybersecurity project demonstrating authenticated cryptographic encapsulation paired with spatial least-significant-bit steganography.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown(
            """
            <div class="cyber-card" style="height: 100%;">
                <h4 style="color: #00f0ff; margin-top: 0;">Technology Stack</h4>
                <ul style="padding-left: 1.2rem; margin: 0; color: #dfe2ee; line-height: 1.8; font-family: 'JetBrains Mono', monospace; font-size: 12px;">
                    <li>Python 3.13</li>
                    <li>Streamlit (Modern HUD Runtime)</li>
                    <li>Pillow (PIL Imaging Engine)</li>
                    <li>Cryptography (AES-256-GCM / PBKDF2)</li>
                    <li>NumPy (Vectorized Pixel Operations)</li>
                    <li>Pytest (Automated Verification Suite)</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_t2:
        st.markdown(
            """
            <div class="cyber-card" style="height: 100%;">
                <h4 style="color: #4edea3; margin-top: 0;">Security Features</h4>
                <ul style="padding-left: 1.2rem; margin: 0; color: #dfe2ee; line-height: 1.8; font-family: 'JetBrains Mono', monospace; font-size: 12px;">
                    <li>AES-256-GCM Authenticated Encryption</li>
                    <li>PBKDF2-HMAC-SHA256 (600,000 Iterations)</li>
                    <li>RGB Least Significant Bit Embedding</li>
                    <li>Real-time MSE / PSNR Steganalytics</li>
                    <li>Memory Isolated Round-trip Verification</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
