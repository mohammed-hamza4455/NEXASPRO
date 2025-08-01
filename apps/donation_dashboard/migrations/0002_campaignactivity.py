# Generated by Django 4.2.7 on 2025-07-22 06:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('donation_dashboard', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CampaignActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_type', models.CharField(choices=[('campaign_created', 'Campaign Created'), ('campaign_updated', 'Campaign Updated'), ('donation_received', 'Donation Received'), ('volunteer_joined', 'Volunteer Joined'), ('milestone_reached', 'Milestone Reached'), ('campaign_shared', 'Campaign Shared'), ('report_generated', 'Report Generated'), ('campaign_completed', 'Campaign Completed')], max_length=20)),
                ('description', models.TextField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='donation_dashboard.donationcampaign')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='campaign_activities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Campaign Activity',
                'verbose_name_plural': 'Campaign Activities',
                'ordering': ['-created_at'],
            },
        ),
    ]
