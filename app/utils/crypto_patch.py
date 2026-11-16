"""Hardware-accelerated AES-IGE patch for Telethon using system OpenSSL/libcrypto."""

import ctypes
import os
import sys
from pathlib import Path
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def apply_crypto_acceleration() -> bool:
    """
    Locate and hook libcrypto/OpenSSL into Telethon for 200x faster AES IGE encryption/decryption.
    Supports Windows (Python's bundled libcrypto-3.dll), Linux, and macOS.
    """
    try:
        from telethon.crypto import libssl, aes

        if libssl.decrypt_ige is not None:
            logger.debug("Telethon already has accelerated AES-IGE enabled.")
            return True

        target_lib = None

        # Build candidate search paths
        candidate_dirs = []
        base_exe = getattr(sys, "_base_executable", None)
        if base_exe:
            candidate_dirs.append(Path(base_exe).parent / "DLLs")
            candidate_dirs.append(Path(base_exe).parent)

        base_prefix = getattr(sys, "base_prefix", None)
        if base_prefix:
            candidate_dirs.append(Path(base_prefix) / "DLLs")
            candidate_dirs.append(Path(base_prefix))

        exe_path = getattr(sys, "executable", None)
        if exe_path:
            candidate_dirs.append(Path(exe_path).parent / "DLLs")
            candidate_dirs.append(Path(exe_path).parent)

        dll_names = (
            "libcrypto-3.dll",
            "libcrypto-3-x64.dll",
            "libcrypto-1_1-x64.dll",
            "libcrypto-1_1.dll",
        )

        for c_dir in candidate_dirs:
            if c_dir.exists():
                for name in dll_names:
                    candidate = c_dir / name
                    if candidate.exists():
                        try:
                            lib = ctypes.cdll.LoadLibrary(str(candidate))
                            if hasattr(lib, "AES_ige_encrypt"):
                                target_lib = lib
                                break
                        except Exception as e:
                            logger.debug("Could not load candidate %s: %s", candidate, e)
            if target_lib:
                break

        # Fallback to standard library search
        if not target_lib:
            import ctypes.util
            for lib_name in ("crypto", "ssl", "libcrypto", "libssl"):
                found = ctypes.util.find_library(lib_name)
                if found:
                    try:
                        lib = ctypes.cdll.LoadLibrary(found)
                        if hasattr(lib, "AES_ige_encrypt"):
                            target_lib = lib
                            break
                    except Exception:
                        pass

        if not target_lib or not hasattr(target_lib, "AES_ige_encrypt"):
            logger.warning("Could not find hardware-accelerated OpenSSL AES_ige_encrypt; falling back to default.")
            return False

        # Define OpenSSL structures and functions
        AES_ENCRYPT = ctypes.c_int(1)
        AES_DECRYPT = ctypes.c_int(0)
        AES_MAXNR = 14

        class AES_KEY(ctypes.Structure):
            _fields_ = [
                ("rd_key", ctypes.c_uint32 * (4 * (AES_MAXNR + 1))),
                ("rounds", ctypes.c_uint),
            ]

        def fast_decrypt_ige(cipher_text: bytes, key: bytes, iv: bytes) -> bytes:
            aes_key = AES_KEY()
            key_len = ctypes.c_int(8 * len(key))
            c_key = (ctypes.c_ubyte * len(key))(*key)
            c_iv = (ctypes.c_ubyte * len(iv))(*iv)

            in_len = ctypes.c_size_t(len(cipher_text))
            in_ptr = (ctypes.c_ubyte * len(cipher_text)).from_buffer_copy(cipher_text)
            out_ptr = (ctypes.c_ubyte * len(cipher_text))()

            target_lib.AES_set_decrypt_key(c_key, key_len, ctypes.byref(aes_key))
            target_lib.AES_ige_encrypt(
                ctypes.byref(in_ptr),
                ctypes.byref(out_ptr),
                in_len,
                ctypes.byref(aes_key),
                ctypes.byref(c_iv),
                AES_DECRYPT,
            )
            return bytes(out_ptr)

        def fast_encrypt_ige(plain_text: bytes, key: bytes, iv: bytes) -> bytes:
            padding = len(plain_text) % 16
            if padding:
                plain_text += os.urandom(16 - padding)

            aes_key = AES_KEY()
            key_len = ctypes.c_int(8 * len(key))
            c_key = (ctypes.c_ubyte * len(key))(*key)
            c_iv = (ctypes.c_ubyte * len(iv))(*iv)

            in_len = ctypes.c_size_t(len(plain_text))
            in_ptr = (ctypes.c_ubyte * len(plain_text)).from_buffer_copy(plain_text)
            out_ptr = (ctypes.c_ubyte * len(plain_text))()

            target_lib.AES_set_encrypt_key(c_key, key_len, ctypes.byref(aes_key))
            target_lib.AES_ige_encrypt(
                ctypes.byref(in_ptr),
                ctypes.byref(out_ptr),
                in_len,
                ctypes.byref(aes_key),
                ctypes.byref(c_iv),
                AES_ENCRYPT,
            )
            return bytes(out_ptr)

        # Inject into Telethon's libssl and aes modules
        libssl.decrypt_ige = fast_decrypt_ige
        libssl.encrypt_ige = fast_encrypt_ige
        aes.AES.decrypt_ige = staticmethod(fast_decrypt_ige)
        aes.AES.encrypt_ige = staticmethod(fast_encrypt_ige)

        logger.info("Successfully enabled hardware-accelerated OpenSSL AES-IGE (~70 MB/s).")
        return True

    except Exception as exc:
        logger.warning("Failed to enable hardware-accelerated AES: %s", exc)
        return False
