from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='lineage.Agent')
def create_index_profile_for_lineage_agent(sender, instance, created, **kwargs):
    try:
        from .models import IndexProfile
    except Exception:
        return
    if created:
        try:
            IndexProfile.objects.create(
                full_name=(instance.real_name or instance.alias or 'Unknown').strip(),
                aliases=instance.alias or '',
                classification=IndexProfile.Classification.ASSET_TALON,
                status=IndexProfile.Status.ACTIVE,
                threat_level=IndexProfile.ThreatLevel.NONE,
                biography=instance.summary or ''
            )
        except Exception:
            # Avoid blocking agent creation on failures
            pass

