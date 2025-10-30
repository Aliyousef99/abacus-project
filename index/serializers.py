from rest_framework import serializers
from .models import IndexProfile, IndexAffiliation


class IndexProfileSerializer(serializers.ModelSerializer):
    affiliations = serializers.PrimaryKeyRelatedField(many=True, queryset=__import__('scales.models', fromlist=['Faction']).Faction.objects.all(), required=False)
    affiliation_names = serializers.SerializerMethodField()
    affiliations_detail = serializers.SerializerMethodField()
    full_name = serializers.CharField(required=True)
    aliases = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    classification = serializers.ChoiceField(choices=IndexProfile.Classification.choices, required=False, allow_null=True)
    status = serializers.ChoiceField(choices=IndexProfile.Status.choices, required=False, allow_null=True)
    threat_level = serializers.ChoiceField(choices=IndexProfile.ThreatLevel.choices, required=False, allow_null=True)
    biography = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    strengths = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    weaknesses = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    known_locations = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    known_vehicles = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    surveillance_urls = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = IndexProfile
        fields = [
            'id', 'full_name', 'aliases', 'classification', 'affiliations', 'affiliation_names', 'affiliations_detail',
            'status', 'threat_level', 'biography', 'strengths', 'weaknesses',
            'known_locations', 'known_vehicles', 'surveillance_urls', 'picture_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'affiliation_names']

    def get_affiliation_names(self, obj):
        try:
            return [f.name for f in obj.affiliations.all()]
        except Exception:
            return []

    def get_affiliations_detail(self, obj):
        try:
            links = IndexAffiliation.objects.select_related('faction').filter(profile=obj)
            return [{ 'id': l.faction_id, 'name': getattr(l.faction, 'name', ''), 'level': l.level or '' } for l in links]
        except Exception:
            return []

    def create(self, validated_data):
        # Extract M2M affiliations to add after creating the profile
        affiliations = validated_data.pop('affiliations', []) if 'affiliations' in validated_data else []
        profile = IndexProfile.objects.create(**validated_data)
        if affiliations:
            profile.affiliations.set(affiliations)
        return profile

    def update(self, instance, validated_data):
        affiliations = validated_data.pop('affiliations', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if affiliations is not None:
            instance.affiliations.set(affiliations)
        return instance
