from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models.signals import post_save
from django.utils.timezone import localtime, now

class Post(models.Model):
    user = models.ForeignKey(User,related_name='posts', on_delete=models.DO_NOTHING) 
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField('Tag', blank=True)
    likes = models.ManyToManyField(User, related_name='post_like', blank=True)
    shares = models.ManyToManyField(User, related_name='post_share', blank=True)

    class Meta:
        ordering = ['-created_at']

    def likes_counter(self):
        return self.likes.count()
    def shares_counter(self):
        return self.shares.count()
    
    def timetrack(self):
        delta = now() - self.created_at
        seconds = delta.total_seconds()
        minutes = int(seconds // 60)
        hours = int(seconds // 3600)

        if seconds < 60:
            return "agora"
        elif minutes == 1:
            return "Há 1 minuto"
        elif minutes < 60:
            return f"Há {minutes} minutos"
        elif hours == 1:
            return "Há 1 hora"
        elif hours < 24:
            return f"Há {hours} horas"
        else:
            return localtime(self.created_at).strftime('%d/%m/%Y %H:%M')

    def __str__(self):
        return (
            f"{self.user.username} "
            f"({localtime(self.created_at).strftime('%d/%m/%Y %H:%M')}): "
            f"{self.content[:20]}..."
        )

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=20, blank=True, null=True)
    follows = models.ManyToManyField('self', related_name='followed_by', symmetrical=False, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    profile_pic = models.ImageField(upload_to='smalltalk/profile_pics', blank=True, null=True)
    cover_pic = models.ImageField(upload_to='smalltalk/cover_pics', blank=True, null=True)
    location = models.CharField(max_length=20, blank=True, null=True) 
    description = models.TextField(max_length=80, blank=True, null=True)

    def following_count(self):
        return self.follows.exclude(id=self.id).count()

    def followers_count(self):
        return self.followed_by.exclude(id=self.id).count()

    def __str__(self):
        return self.user.username + " - " + self.user.email

def create_profile(sender, instance, created, **kwargs):
    if created:
        with transaction.atomic():
            # Check if profile already exists
            if not hasattr(instance, 'profile'):
                Profile.objects.create(user=instance)

post_save.connect(create_profile, sender=User)

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def mentions_count(self):
        return Post.objects.filter(tags__name=self.name).count()
    def __str__(self):
        return f"{self.name}"
