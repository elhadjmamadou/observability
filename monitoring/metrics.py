"""
Collecteur Prometheus personnalisé pour FreeJobGN.

Expose les métriques métier en interrogeant la base de données à chaque
scrape Prometheus (toutes les 15 s par défaut).  Les métriques
d'infrastructure HTTP/DB sont gérées par django-prometheus.
"""

from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import Collector


class FreeJobGNCollector(Collector):
    """Collecteur de métriques métier FreeJobGN."""

    def describe(self):
        # Retourne les descripteurs sans interroger la DB (appelé au register()).
        yield GaugeMetricFamily("freejobgn_users_total", "")
        yield GaugeMetricFamily("freejobgn_active_users_total", "")
        yield GaugeMetricFamily("freejobgn_projects_total", "")
        yield GaugeMetricFamily("freejobgn_contracts_total", "")
        yield GaugeMetricFamily("freejobgn_payment_transactions_total", "")
        yield GaugeMetricFamily("freejobgn_webhooks_total", "")
        yield GaugeMetricFamily("freejobgn_subscriptions_total", "")
        yield GaugeMetricFamily("freejobgn_active_subscriptions_by_tier", "")
        yield GaugeMetricFamily("freejobgn_wallet_transactions_total", "")

    def collect(self):
        yield from self._collect_users()
        yield from self._collect_projects()
        yield from self._collect_contracts()
        yield from self._collect_payments()
        yield from self._collect_webhooks()
        yield from self._collect_subscriptions()
        yield from self._collect_wallet()

    # ------------------------------------------------------------------ #
    # Users
    # ------------------------------------------------------------------ #

    def _collect_users(self):
        from core.choices import UserRole
        from users.models import User

        g = GaugeMetricFamily(
            "freejobgn_users_total",
            "Nombre total d'utilisateurs par rôle",
            labels=["role"],
        )
        for role in UserRole.values:
            g.add_metric([role], User.objects.filter(role=role).count())
        yield g

        active = GaugeMetricFamily(
            "freejobgn_active_users_total",
            "Utilisateurs actifs (is_active=True) par rôle",
            labels=["role"],
        )
        for role in UserRole.values:
            active.add_metric([role], User.objects.filter(role=role, is_active=True).count())
        yield active

    # ------------------------------------------------------------------ #
    # Projects
    # ------------------------------------------------------------------ #

    def _collect_projects(self):
        from core.choices import ProjectStatus
        from projects.models import Project

        g = GaugeMetricFamily(
            "freejobgn_projects_total",
            "Nombre de projets par statut",
            labels=["status"],
        )
        for status in ProjectStatus.values:
            g.add_metric([status], Project.objects.filter(status=status).count())
        yield g

    # ------------------------------------------------------------------ #
    # Contracts
    # ------------------------------------------------------------------ #

    def _collect_contracts(self):
        from core.choices import ContractStatus
        from projects.models import Contract

        g = GaugeMetricFamily(
            "freejobgn_contracts_total",
            "Nombre de contrats par statut",
            labels=["status"],
        )
        for status in ContractStatus.values:
            g.add_metric([status], Contract.objects.filter(status=status).count())
        yield g

    # ------------------------------------------------------------------ #
    # Payments
    # ------------------------------------------------------------------ #

    def _collect_payments(self):
        from core.choices import PaymentStatus
        from payments.models import PaymentTransaction

        g = GaugeMetricFamily(
            "freejobgn_payment_transactions_total",
            "Transactions de paiement par statut",
            labels=["status"],
        )
        for status in PaymentStatus.values:
            g.add_metric([status], PaymentTransaction.objects.filter(status=status).count())
        yield g

    # ------------------------------------------------------------------ #
    # Webhooks
    # ------------------------------------------------------------------ #

    def _collect_webhooks(self):
        from payments.models import WebhookEvent

        g = GaugeMetricFamily(
            "freejobgn_webhooks_total",
            "Événements webhook par état de traitement",
            labels=["state"],
        )
        g.add_metric(
            ["success"],
            WebhookEvent.objects.filter(processed=True, last_error__isnull=True).count(),
        )
        g.add_metric(
            ["invalid_signature"],
            WebhookEvent.objects.filter(last_error="INVALID_SIGNATURE").count(),
        )
        g.add_metric(
            ["error"],
            WebhookEvent.objects.filter(
                processed=True,
                last_error__isnull=False,
            )
            .exclude(last_error="INVALID_SIGNATURE")
            .count(),
        )
        g.add_metric(
            ["pending"],
            WebhookEvent.objects.filter(processed=False).count(),
        )
        yield g

    # ------------------------------------------------------------------ #
    # Subscriptions
    # ------------------------------------------------------------------ #

    def _collect_subscriptions(self):
        from core.choices import PlanTier, SubscriptionStatus
        from subscriptions.models import Subscription

        by_status = GaugeMetricFamily(
            "freejobgn_subscriptions_total",
            "Abonnements par statut",
            labels=["status"],
        )
        for status in SubscriptionStatus.values:
            by_status.add_metric([status], Subscription.objects.filter(status=status).count())
        yield by_status

        by_tier = GaugeMetricFamily(
            "freejobgn_active_subscriptions_by_tier",
            "Abonnements actifs par niveau de plan",
            labels=["tier"],
        )
        for tier in PlanTier.values:
            count = Subscription.objects.filter(
                status=SubscriptionStatus.ACTIVE,
                plan__tier=tier,
            ).count()
            by_tier.add_metric([tier], count)
        yield by_tier

    # ------------------------------------------------------------------ #
    # Wallet
    # ------------------------------------------------------------------ #

    def _collect_wallet(self):
        from core.choices import WalletTransactionType
        from wallet.models import WalletTransaction

        g = GaugeMetricFamily(
            "freejobgn_wallet_transactions_total",
            "Transactions wallet par type",
            labels=["type"],
        )
        for tx_type in WalletTransactionType.values:
            g.add_metric(
                [tx_type],
                WalletTransaction.objects.filter(transaction_type=tx_type).count(),
            )
        yield g
