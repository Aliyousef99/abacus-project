from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

from lineage.models import Agent
from scales.models import Faction
from codex.models import CodexEntry

class Operation(models.Model):
    STATUS_CHOICES = [
        ('PLANNING', 'Planning'),
        ('ACTIVE', 'Active'),
        ('CONCLUDED - SUCCESS', 'Concluded - Success'),
        ('CONCLUDED - FAILURE', 'Concluded - Failure'),
        ('COMPROMISED', 'Compromised'),
    ]

    RISK_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    codename = models.CharField(max_length=100, unique=True)
    objective = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PLANNING')
    
    # Relationships
    targets = models.ManyToManyField(Faction, related_name='operations', blank=True)
    personnel = models.ManyToManyField(Agent, related_name='operations', blank=True)
    contingencies = models.ManyToManyField(CodexEntry, related_name='operations', blank=True)
    assets = models.TextField(blank=True, help_text="Placeholder for assets from The Vault.")

    # Dynamic Analysis Fields
    success_probability = models.IntegerField(
        default=50, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    collateral_risk = models.CharField(max_length=10, choices=RISK_CHOICES, default='MEDIUM')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    after_action_report = models.TextField(blank=True)

    def __str__(self):
        return self.codename

class OperationLog(models.Model):
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Log for {self.operation.codename} at {self.timestamp}"

class Asset(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('ALLOCATED', 'Allocated'),
        ('UNAVAILABLE', 'Unavailable'),
    ]
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')

    def __str__(self):
        return f"{self.name} ({self.type})"

class AssetRequisition(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
    ]
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='requisitions')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='requisitions')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='asset_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='asset_approvals')
    decided_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('operation', 'asset')

    def __str__(self):
        return f"{self.asset} for {self.operation} [{self.status}]"
