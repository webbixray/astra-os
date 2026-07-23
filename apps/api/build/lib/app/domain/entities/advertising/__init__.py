"""Advertising domain entities."""

from app.domain.entities.advertising.ad_account import AdAccount, Platform, ConnectionStatus

# Alias for backward compatibility — routes.py imports AdPlatform
AdPlatform = Platform

__all__ = ["AdAccount", "Platform", "AdPlatform", "ConnectionStatus"]
