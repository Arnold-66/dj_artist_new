from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_ADMIN = "admin"
    ROLE_OPERATOR = "operator"
    ROLE_DJ = "dj"
    ROLE_KIT_USER = "kit_user"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Administrator"),
        (ROLE_OPERATOR, "Operator"),
        (ROLE_DJ, "DJ"),
        (ROLE_KIT_USER, "Press Kit User"),
    ]

    # ✅ Unique email
    email = models.EmailField(unique=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_KIT_USER)

    dj_profile = models.OneToOneField(
        "core.ArtistProfile",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="owner_user",
        help_text="Required for DJ-role users. Links this account to one artist.",
    )
    managed_artists = models.ManyToManyField(
        "core.ArtistProfile",
        blank=True,
        related_name="operators",
        help_text="DJs this operator is assigned to manage.",
    )

    is_subscribed = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(default=timezone.now, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["username"]

    # ---------- Role helpers ----------
    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_operator_role(self):
        return self.role == self.ROLE_OPERATOR

    @property
    def is_dj_role(self):
        return self.role == self.ROLE_DJ

    @property
    def is_kit_user(self):
        return self.role == self.ROLE_KIT_USER

    @property
    def is_management_user(self):
        """Admins / operators / DJs — the people who use the dashboard."""
        return self.is_admin_role or self.is_operator_role or self.is_dj_role or self.is_staff

    @property
    def email_verified(self):
        return self.emailaddress_set.filter(verified=True).exists()

    @property
    def can_download(self):
        if self.is_management_user:
            return True
        return self.is_active and self.email_verified

    @property
    def can_manage_events(self):
        """Only admins and operators may create/edit/delete events."""
        return self.is_admin_role or self.is_operator_role


    # ---------- Scope helpers ----------
    def accessible_artists(self):
        from apps.core.models import ArtistProfile
        if self.is_admin_role:
            return ArtistProfile.objects.all()
        if self.is_dj_role and self.dj_profile_id:
            return ArtistProfile.objects.filter(pk=self.dj_profile_id)
        if self.is_operator_role:
            return self.managed_artists.all()
        return ArtistProfile.objects.none()

    def can_manage_artist(self, artist):
        if not artist:
            return False
        if self.is_admin_role:
            return True
        if self.is_dj_role and self.dj_profile_id == artist.pk:
            return True
        if self.is_operator_role and self.managed_artists.filter(pk=artist.pk).exists():
            return True
        return False

    def can_manage_role(self, other_user):
        if not self.is_admin_role:
            return False
        if other_user.is_superuser and other_user != self:
            return False
        return True

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"