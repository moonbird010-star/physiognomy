"""메일 발송: 관상 풀이 결과를 SMTP 로 보낸다. 발송 계정은 .env 에서 읽는다.

.env 설정:
    SMTP_HOST      예: smtp.gmail.com
    SMTP_PORT      587 (STARTTLS) 또는 465 (SSL). 기본 587
    SMTP_USER      로그인 계정 (예: Gmail 주소)
    SMTP_PASSWORD  비밀번호 (Gmail 은 2단계 인증 후 만든 앱 비밀번호)
    MAIL_FROM      보내는 사람 주소 (없으면 SMTP_USER)

악용을 막기 위해 받는 주소는 하나만, 같은 접속처는 1시간에 정해진 수까지만 보낸다.
메일 내용·주소는 로그에 남기지 않는다.
"""
import os
import re
import smtplib
import ssl
import threading
import time
from datetime import datetime
from email.message import EmailMessage

from src.shared.config import KST
from src.sharing.templates import SUBJECT, mail_body

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
MAX_HTML_BYTES = 3_000_000  # 첨부 결과 파일 크기 상한 (사진을 뺀 결과는 수백 KB)
LIMIT_PER_HOUR = 5

_sent: dict[str, list[float]] = {}
_lock = threading.Lock()


class MailError(Exception):
    """사용자에게 그대로 보여 줄 수 있는 발송 실패 이유."""


def configured() -> bool:
    """SMTP 발송 설정이 .env 에 있는지 알려 준다."""
    return all(os.getenv(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"))


def _check_rate(client_key: str) -> None:
    """같은 접속처가 1시간에 LIMIT_PER_HOUR 통을 넘게 보내지 못하게 한다."""
    now = time.time()
    with _lock:
        recent = [t for t in _sent.get(client_key, []) if now - t < 3600]
        if len(recent) >= LIMIT_PER_HOUR:
            raise MailError(f"메일은 1시간에 {LIMIT_PER_HOUR}통까지 보낼 수 있어요. 잠시 뒤에 다시 시도해 주세요.")
        recent.append(now)
        _sent[client_key] = recent


def send_result(to: str, html: str, summary: str, client_key: str) -> None:
    """관상 결과를 to 주소로 보낸다. 본문은 요약, 첨부는 결과 HTML 파일이다. 실패하면 MailError."""
    to = (to or "").strip()
    if not EMAIL_RE.match(to):
        raise MailError("이메일 주소 형식이 올바르지 않아요. 예: name@example.com")
    if not configured():
        raise MailError("메일 발송 설정이 아직 없어요. 관리자가 .env 에 SMTP 정보를 넣어야 해요.")
    if not html or len(html.encode("utf-8")) > MAX_HTML_BYTES:
        raise MailError("보낼 결과가 없거나 너무 커요.")
    _check_rate(client_key)

    sender = os.getenv("MAIL_FROM") or os.environ["SMTP_USER"]
    msg = EmailMessage()
    msg["Subject"] = SUBJECT
    msg["From"] = sender
    msg["To"] = to
    msg.set_content(mail_body(summary[:1500]))
    filename = f"관상결과_{datetime.now(KST).date().isoformat()}.html"
    msg.add_attachment(html.encode("utf-8"), maintype="text", subtype="html", filename=filename)

    host, port = os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT", "587"))
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=30) as smtp:
                smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                smtp.starttls(context=ssl.create_default_context())
                smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
                smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError as error:
        raise MailError("메일 계정 로그인에 실패했어요. 관리자가 SMTP 계정 정보를 확인해야 해요.") from error
    except (smtplib.SMTPException, OSError) as error:
        raise MailError("메일을 보내지 못했어요. 잠시 뒤에 다시 시도해 주세요.") from error
