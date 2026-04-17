"""邮件发送工具"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from config import settings

logger = logging.getLogger("email")


def send_verification_email(to_email: str, code: str, expire_minutes: int = 5) -> tuple[bool, str]:
    """
    发送邮箱验证码
    返回: (是否成功, 错误信息)
    """
    if not settings.smtp_user or not settings.smtp_password:
        logger.error("邮件配置未设置，请在.env中配置 SMTP_USER 和 SMTP_PASSWORD")
        return False, "邮件服务未配置"

    subject = "Aitbake - 注册验证码"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px; background: #f9f9f9; border-radius: 8px;">
        <h2 style="color: #3b82f6; margin-bottom: 8px;">Aitbake</h2>
        <p style="color: #555; margin-bottom: 24px;">您正在注册账户，验证码如下：</p>
        <div style="background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px; text-align: center; margin-bottom: 24px;">
            <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #1f2937;">{code}</span>
        </div>
        <p style="color: #888; font-size: 13px;">验证码 <strong>{expire_minutes} 分钟</strong>内有效，请勿泄露给他人。</p>
        <p style="color: #bbb; font-size: 12px; margin-top: 16px;">如非本人操作，请忽略此邮件。</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = settings.smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if settings.smtp_port == 465:
            # SSL
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_user, to_email, msg.as_string())
        else:
            # TLS (587)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_user, to_email, msg.as_string())

        logger.info(f"验证码邮件已发送至 {to_email}")
        return True, "发送成功"

    except smtplib.SMTPAuthenticationError:
        logger.error(f"邮件认证失败，请检查 SMTP_USER 和 SMTP_PASSWORD")
        return False, "邮件服务认证失败，请联系管理员"
    except smtplib.SMTPException as e:
        logger.error(f"邮件发送失败: {e}")
        return False, "邮件发送失败，请稍后重试"
    except Exception as e:
        logger.error(f"邮件发送异常: {e}")
        return False, "邮件发送失败，请稍后重试"


def send_push_approved_email(to_email: str, ktt_name: str) -> tuple[bool, str]:
    """
    发送推送申请审核通过通知邮件
    返回: (是否成功, 错误信息)
    邮件发送失败时仅记录日志，不抛出异常
    """
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("邮件配置未设置，跳过发送审核通过通知邮件")
        return False, "邮件服务未配置"

    subject = "Aitbake - 您的推送申请已通过审核"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px; background: #f9f9f9; border-radius: 8px;">
        <h2 style="color: #3b82f6; margin-bottom: 8px;">Aitbake</h2>
        <p style="color: #555; margin-bottom: 16px;">您好，您提交的黑名单推送申请已通过审核。</p>
        <div style="background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
            <p style="margin: 0; color: #1f2937;"><strong>KTT 姓名：</strong>{ktt_name}</p>
            <p style="margin: 8px 0 0; color: #16a34a;"><strong>审核结果：</strong>✅ 已通过，该条目已加入系统黑名单</p>
        </div>
        <p style="color: #bbb; font-size: 12px; margin-top: 16px;">如有疑问，请联系管理员。</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = settings.smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_user, to_email, msg.as_string())
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_user, to_email, msg.as_string())

        logger.info(f"审核通过通知邮件已发送至 {to_email}")
        return True, "发送成功"

    except Exception as e:
        logger.error(f"审核通过通知邮件发送失败: {e}")
        return False, str(e)


def send_push_rejected_email(to_email: str, ktt_name: str, reject_reason: str) -> tuple[bool, str]:
    """
    发送推送申请审核拒绝通知邮件
    返回: (是否成功, 错误信息)
    邮件发送失败时仅记录日志，不抛出异常
    """
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("邮件配置未设置，跳过发送审核拒绝通知邮件")
        return False, "邮件服务未配置"

    subject = "Aitbake - 您的推送申请未通过审核"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px; background: #f9f9f9; border-radius: 8px;">
        <h2 style="color: #3b82f6; margin-bottom: 8px;">Aitbake</h2>
        <p style="color: #555; margin-bottom: 16px;">您好，您提交的黑名单推送申请未通过审核。</p>
        <div style="background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
            <p style="margin: 0; color: #1f2937;"><strong>KTT 姓名：</strong>{ktt_name}</p>
            <p style="margin: 8px 0 0; color: #dc2626;"><strong>审核结果：</strong>❌ 未通过</p>
            <p style="margin: 8px 0 0; color: #555;"><strong>拒绝原因：</strong>{reject_reason}</p>
        </div>
        <p style="color: #888; font-size: 13px;">您可以补充证据后重新提交申请。</p>
        <p style="color: #bbb; font-size: 12px; margin-top: 16px;">如有疑问，请联系管理员。</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = settings.smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_user, to_email, msg.as_string())
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_user, to_email, msg.as_string())

        logger.info(f"审核拒绝通知邮件已发送至 {to_email}")
        return True, "发送成功"

    except Exception as e:
        logger.error(f"审核拒绝通知邮件发送失败: {e}")
        return False, str(e)
