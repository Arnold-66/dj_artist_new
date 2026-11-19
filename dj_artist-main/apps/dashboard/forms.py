from django import forms
from django.contrib.auth import get_user_model

from apps.bookings.models import BookingInquiry
from apps.music.models import Mix
from apps.events.models import Event

User = get_user_model()


# ---------- BOOKINGS ----------
class BookingStatusForm(forms.ModelForm):
    class Meta:
        model = BookingInquiry
        fields = ["status"]
        widgets = {"status": forms.Select(attrs={"class": "form-select"})}


class BookingReplyForm(forms.Form):
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Email subject"}),
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 7, "placeholder": "Write your reply..."}),
    )


# ---------- USERS ----------
class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}), label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}), label="Confirm Password")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "role", "is_staff", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match.")
        if cleaned.get("password1") and len(cleaned["password1"]) < 8:
            raise forms.ValidationError("Password must be at least 8 characters.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_staff = True
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="New Password (leave blank to keep current)",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "role", "is_staff", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get("new_password")
        if pwd:
            if len(pwd) < 8:
                raise forms.ValidationError("Password must be at least 8 characters.")
            user.set_password(pwd)
        if commit:
            user.save()
        return user


# ---------- MUSIC ----------
class MixForm(forms.ModelForm):
    class Meta:
        model = Mix
        fields = [
            "title", "media_type", "platform", "embed_url",
            "audio_file", "cover_image", "description",
            "private_audio_file", "is_featured", "is_published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "media_type": forms.Select(attrs={"class": "form-select"}),
            "platform": forms.TextInput(attrs={"class": "form-control"}),
            "embed_url": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "audio_file": forms.FileInput(attrs={"class": "form-control"}),
            "cover_image": forms.FileInput(attrs={"class": "form-control"}),
            "private_audio_file": forms.FileInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


# ---------- EVENTS ----------
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title", "slug", "event_type", "venue", "city_country",
            "start_at", "end_at", "description", "poster",
            "ticket_url", "is_published", "notify_subscribers",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "event_type": forms.TextInput(attrs={"class": "form-control"}),
            "venue": forms.TextInput(attrs={"class": "form-control"}),
            "city_country": forms.TextInput(attrs={"class": "form-control"}),
            "start_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "poster": forms.FileInput(attrs={"class": "form-control"}),
            "ticket_url": forms.URLInput(attrs={"class": "form-control"}),
        }



# ---------- ARTIST PROFILES ----------
from django.contrib.auth.forms import AuthenticationForm
from apps.core.models import ArtistProfile


class StaffLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Username",
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password",
        })
    )


class DJProfileForm(forms.ModelForm):
    # Only administrators can assign accounts.
    dj_user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="DJ Account",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    operator_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Assigned Operators",
        widget=forms.SelectMultiple(attrs={
            "class": "form-select",
            "size": "5",
        }),
    )

    class Meta:
        model = ArtistProfile
        fields = [
            "stage_name",
            "slug",
            "theme_color",
            "hero_title",
            "hero_kicker",
            "signature_image",
            "tagline",
            "short_bio",
            "full_bio",
            "hero_image",
            "logo",
            "email",
            "phone",
            "instagram_url",
            "facebook_url",
            "tiktok_url",
            "youtube_url",
        ]

        widgets = {
            "stage_name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "theme_color": forms.TextInput(attrs={
                "class": "form-control",
                "type": "color",
            }),
            "hero_title": forms.TextInput(attrs={"class": "form-control"}),
            "hero_kicker": forms.TextInput(attrs={"class": "form-control"}),
            "signature_image": forms.FileInput(attrs={"class": "form-control"}),
            "tagline": forms.TextInput(attrs={"class": "form-control"}),
            "short_bio": forms.Textarea(attrs={
                "class": "form-control", "rows": 3
            }),
            "full_bio": forms.Textarea(attrs={
                "class": "form-control", "rows": 7
            }),
            "hero_image": forms.FileInput(attrs={"class": "form-control"}),
            "logo": forms.FileInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "instagram_url": forms.URLInput(attrs={"class": "form-control"}),
            "facebook_url": forms.URLInput(attrs={"class": "form-control"}),
            "tiktok_url": forms.URLInput(attrs={"class": "form-control"}),
            "youtube_url": forms.URLInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["dj_user"].queryset = User.objects.filter(
            role=User.ROLE_DJ,
            is_active=True,
        ).order_by("username")

        self.fields["operator_users"].queryset = User.objects.filter(
            role=User.ROLE_OPERATOR,
            is_active=True,
        ).order_by("username")

        if self.instance and self.instance.pk:
            owner = User.objects.filter(
                dj_profile=self.instance
            ).first()

            self.fields["dj_user"].initial = owner

            self.fields["operator_users"].initial = (
                self.instance.operators.all()
            )

    def clean_dj_user(self):
        dj_user = self.cleaned_data.get("dj_user")

        if dj_user and dj_user.dj_profile_id:
            if not self.instance.pk or dj_user.dj_profile_id != self.instance.pk:
                raise forms.ValidationError(
                    "This DJ account is already assigned to another artist."
                )

        return dj_user

    def save(self, commit=True):
        old_owner = None

        if self.instance.pk:
            old_owner = User.objects.filter(
                dj_profile=self.instance
            ).first()

        artist = super().save(commit=False)

        if commit:
            artist.save()

            new_owner = self.cleaned_data.get("dj_user")

            # Remove previous DJ assignment if changed.
            if old_owner and old_owner != new_owner:
                old_owner.dj_profile = None
                old_owner.save(update_fields=["dj_profile"])

            # Assign the new DJ.
            if new_owner:
                new_owner.dj_profile = artist
                new_owner.save(update_fields=["dj_profile"])

            # Synchronise assigned operators.
            operators = self.cleaned_data.get("operator_users")
            artist.operators.set(operators)

        return artist


class DJProfileSelfForm(DJProfileForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove account assignment controls entirely.
        self.fields.pop("dj_user")
        self.fields.pop("operator_users")

        
# Compatibility with the names already imported in views.py.
StaffUserForm = UserEditForm
StaffUserCreateForm = UserCreateForm