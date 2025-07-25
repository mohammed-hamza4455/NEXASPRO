"""
Views for volunteer dashboard.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.views import View

from apps.accounts.permissions import VolunteerRequiredMixin, volunteer_required
from .models import (
    VolunteerTask, VolunteerActivity, VolunteerReport, 
    VolunteerSkill, VolunteerAvailability, VolunteerEvent,
    VolunteerEventRegistration, VolunteerResource, VolunteerResourceAccess
)

User = get_user_model()


class VolunteerDashboardView(VolunteerRequiredMixin, View):
    """
    Main volunteer dashboard view.
    """
    
    def get(self, request):
        volunteer = request.user
        
        # Task statistics
        my_tasks = VolunteerTask.objects.filter(assigned_to=volunteer)
        pending_tasks = my_tasks.filter(status='pending').count()
        in_progress_tasks = my_tasks.filter(status='in_progress').count()
        completed_tasks = my_tasks.filter(status='completed').count()
        overdue_tasks = my_tasks.filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        ).count()
        
        # Recent tasks
        recent_tasks = my_tasks.order_by('-updated_at')[:5]
        
        # Hours statistics
        total_hours = VolunteerActivity.objects.filter(
            volunteer=volunteer,
            hours_logged__isnull=False
        ).aggregate(total=Sum('hours_logged'))['total'] or 0
        
        # This month's hours
        this_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_hours = VolunteerActivity.objects.filter(
            volunteer=volunteer,
            activity_date__gte=this_month_start,
            hours_logged__isnull=False
        ).aggregate(total=Sum('hours_logged'))['total'] or 0
        
        # Recent activities
        recent_activities = VolunteerActivity.objects.filter(
            volunteer=volunteer
        ).order_by('-activity_date')[:5]
        
        # Report statistics
        my_reports = VolunteerReport.objects.filter(volunteer=volunteer)
        draft_reports = my_reports.filter(status='draft').count()
        pending_reports = my_reports.filter(status='submitted').count()
        approved_reports = my_reports.filter(status='approved').count()
        
        # Upcoming deadlines
        upcoming_deadlines = my_tasks.filter(
            due_date__isnull=False,
            due_date__gte=timezone.now(),
            status__in=['pending', 'in_progress']
        ).order_by('due_date')[:5]
        
        # Activity chart data for the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_hours = VolunteerActivity.objects.filter(
            volunteer=volunteer,
            activity_date__gte=thirty_days_ago,
            hours_logged__isnull=False
        ).extra(
            select={'day': 'date(activity_date)'}
        ).values('day').annotate(hours=Sum('hours_logged')).order_by('day')
        
        # Upcoming events
        upcoming_events = VolunteerEvent.objects.filter(
            status='upcoming',
            start_date__gte=timezone.now()
        ).order_by('start_date')[:5]
        
        # My registered events
        my_events = VolunteerEvent.objects.filter(
            volunteers_registered=volunteer,
            start_date__gte=timezone.now()
        ).order_by('start_date')[:3]
        
        context = {
            'pending_tasks': pending_tasks,
            'in_progress_tasks': in_progress_tasks,
            'completed_tasks': completed_tasks,
            'overdue_tasks': overdue_tasks,
            'total_hours': total_hours,
            'this_month_hours': this_month_hours,
            'draft_reports': draft_reports,
            'pending_reports': pending_reports,
            'approved_reports': approved_reports,
            'recent_tasks': recent_tasks,
            'recent_activities': recent_activities,
            'upcoming_deadlines': upcoming_deadlines,
            'upcoming_events': upcoming_events,
            'my_events': my_events,
            'daily_hours': list(daily_hours),
        }
        
        return render(request, 'volunteer/dashboard.html', context)


@volunteer_required
def volunteer_dashboard_new(request):
    """
    Enhanced volunteer dashboard with comprehensive features.
    """
    volunteer = request.user
    now = timezone.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Task statistics
    my_tasks = VolunteerTask.objects.filter(assigned_to=volunteer)
    pending_tasks = my_tasks.filter(status='pending').count()
    in_progress_tasks = my_tasks.filter(status='in_progress').count()
    completed_tasks = my_tasks.filter(status='completed').count()
    overdue_tasks = my_tasks.filter(
        due_date__lt=now,
        status__in=['pending', 'in_progress']
    ).count()
    
    # Recent tasks for dashboard
    recent_tasks = my_tasks.order_by('-updated_at')[:5]
    
    # Hours statistics
    total_hours = VolunteerActivity.objects.filter(
        volunteer=volunteer,
        hours_logged__isnull=False
    ).aggregate(total=Sum('hours_logged'))['total'] or 0
    
    # Monthly statistics
    monthly_hours = VolunteerActivity.objects.filter(
        volunteer=volunteer,
        activity_date__gte=this_month_start,
        hours_logged__isnull=False
    ).aggregate(total=Sum('hours_logged'))['total'] or 0
    
    monthly_tasks = my_tasks.filter(
        completion_date__gte=this_month_start,
        status='completed'
    ).count()
    
    # Event statistics
    all_events = VolunteerEvent.objects.filter(
        status__in=['upcoming', 'active']
    ).order_by('start_date')
    
    upcoming_events = all_events.filter(
        start_date__gte=now
    )[:10]
    
    # My registered events
    my_event_registrations = VolunteerEventRegistration.objects.filter(
        volunteer=volunteer
    ).values_list('event_id', flat=True)
    
    my_events = all_events.filter(id__in=my_event_registrations)
    
    monthly_events = my_events.filter(
        start_date__gte=this_month_start,
        start_date__lt=now
    ).count()
    
    events_attended = VolunteerEventRegistration.objects.filter(
        volunteer=volunteer,
        attendance_status='attended'
    ).count()
    
    # Skills
    my_skills = VolunteerSkill.objects.filter(volunteer=volunteer)
    
    # Calculate impact score (simple algorithm)
    impact_score = (
        completed_tasks * 10 +
        int(total_hours) * 2 +
        events_attended * 5 +
        my_skills.count() * 3
    )
    
    context = {
        # Task stats
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_tasks': recent_tasks,
        'my_tasks': my_tasks,
        
        # Hour stats
        'total_hours': total_hours,
        'monthly_hours': monthly_hours,
        
        # Monthly stats
        'monthly_tasks': monthly_tasks,
        'monthly_events': monthly_events,
        
        # Events
        'upcoming_events': upcoming_events,
        'all_events': all_events,
        'my_events': my_events,
        'events_attended': events_attended,
        
        # Skills and profile
        'my_skills': my_skills,
        
        # Impact
        'impact_score': impact_score,
        
        # Helper
        'now': now,
    }
    
    return render(request, 'volunteer/dashboard.html', context)


@volunteer_required
@require_http_methods(["POST"])
def update_task_status(request, task_id):
    """
    Update task status via AJAX.
    """
    try:
        task = get_object_or_404(VolunteerTask, id=task_id, assigned_to=request.user)
        new_status = request.POST.get('status')
        
        if new_status not in ['pending', 'in_progress', 'completed', 'cancelled']:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
        
        task.status = new_status
        if new_status == 'completed':
            task.completion_date = timezone.now()
        task.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Task status updated to {new_status}',
            'new_status': new_status
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@volunteer_required
@require_http_methods(["POST"])
def request_task(request):
    """
    Request a new task via AJAX.
    """
    try:
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', 'medium')
        
        if not title or not description:
            return JsonResponse({'success': False, 'error': 'Title and description are required'})
        
        # Create task request (pending approval)
        task = VolunteerTask.objects.create(
            title=title,
            description=description,
            assigned_to=request.user,
            priority=priority,
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Task request submitted successfully!',
            'task_id': task.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@volunteer_required
@require_http_methods(["POST"])
def register_for_event(request, event_id):
    """
    Register for an event via AJAX.
    """
    try:
        event = get_object_or_404(VolunteerEvent, id=event_id)
        
        # Check if already registered
        existing_registration = VolunteerEventRegistration.objects.filter(
            volunteer=request.user,
            event=event
        ).first()
        
        if existing_registration:
            return JsonResponse({'success': False, 'error': 'Already registered for this event'})
        
        # Check if event is full
        if event.max_participants:
            current_registrations = VolunteerEventRegistration.objects.filter(event=event).count()
            if current_registrations >= event.max_participants:
                return JsonResponse({'success': False, 'error': 'Event is full'})
        
        # Create registration
        VolunteerEventRegistration.objects.create(
            volunteer=request.user,
            event=event,
            registration_date=timezone.now(),
            status='registered'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully registered for {event.title}!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@volunteer_required
@require_http_methods(["POST"])
def add_skill(request):
    """
    Add a skill via AJAX.
    """
    try:
        skill_name = request.POST.get('skill_name', '').strip()
        skill_level = request.POST.get('skill_level', 'beginner')
        
        if not skill_name:
            return JsonResponse({'success': False, 'error': 'Skill name is required'})
        
        # Check if skill already exists
        existing_skill = VolunteerSkill.objects.filter(
            volunteer=request.user,
            skill_name__iexact=skill_name
        ).first()
        
        if existing_skill:
            # Update existing skill
            existing_skill.proficiency_level = skill_level
            existing_skill.save()
            message = 'Skill updated successfully!'
        else:
            # Create new skill
            VolunteerSkill.objects.create(
                volunteer=request.user,
                skill_name=skill_name,
                proficiency_level=skill_level
            )
            message = 'Skill added successfully!'
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@volunteer_required
@require_http_methods(["POST"])
def save_availability(request):
    """
    Save volunteer availability via AJAX.
    """
    try:
        days = request.POST.getlist('days')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        # Clear existing availability
        VolunteerAvailability.objects.filter(volunteer=request.user).delete()
        
        # Create new availability records
        for day in days:
            VolunteerAvailability.objects.create(
                volunteer=request.user,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time,
                is_available=True
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Availability saved successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@volunteer_required
def volunteer_dashboard(request):
    """
    Function-based volunteer dashboard view.
    """
    volunteer = request.user
    
    # Task statistics
    my_tasks = VolunteerTask.objects.filter(assigned_to=volunteer)
    pending_tasks = my_tasks.filter(status='pending').count()
    in_progress_tasks = my_tasks.filter(status='in_progress').count()
    completed_tasks = my_tasks.filter(status='completed').count()
    overdue_tasks = my_tasks.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    ).count()
    
    # Recent tasks
    recent_tasks = my_tasks.order_by('-updated_at')[:5]
    
    # Hours statistics
    total_hours = VolunteerActivity.objects.filter(
        volunteer=volunteer,
        hours_logged__isnull=False
    ).aggregate(total=Sum('hours_logged'))['total'] or 0
    
    # This month's hours
    this_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_hours = VolunteerActivity.objects.filter(
        volunteer=volunteer,
        activity_date__gte=this_month_start,
        hours_logged__isnull=False
    ).aggregate(total=Sum('hours_logged'))['total'] or 0
    
    # Recent activities
    recent_activities = VolunteerActivity.objects.filter(
        volunteer=volunteer
    ).order_by('-activity_date')[:5]
    
    # Report statistics
    my_reports = VolunteerReport.objects.filter(volunteer=volunteer)
    draft_reports = my_reports.filter(status='draft').count()
    pending_reports = my_reports.filter(status='submitted').count()
    approved_reports = my_reports.filter(status='approved').count()
    
    # Upcoming deadlines
    upcoming_deadlines = my_tasks.filter(
        due_date__isnull=False,
        due_date__gte=timezone.now(),
        status__in=['pending', 'in_progress']
    ).order_by('due_date')[:5]
    
    context = {
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'total_hours': total_hours,
        'this_month_hours': this_month_hours,
        'draft_reports': draft_reports,
        'pending_reports': pending_reports,
        'approved_reports': approved_reports,
        'recent_tasks': recent_tasks,
        'recent_activities': recent_activities,
        'upcoming_deadlines': upcoming_deadlines,
    }
    
    return render(request, 'volunteer/dashboard.html', context)


@volunteer_required
def task_list(request):
    """
    List of assigned tasks for the volunteer.
    """
    volunteer = request.user
    tasks = VolunteerTask.objects.filter(assigned_to=volunteer).order_by('-created_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    # Filter by priority if requested
    priority_filter = request.GET.get('priority')
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': VolunteerTask.STATUS_CHOICES,
        'priority_choices': VolunteerTask.PRIORITY_CHOICES,
        'current_status': status_filter,
        'current_priority': priority_filter,
        'search_query': search_query,
    }
    
    return render(request, 'volunteer/task_list.html', context)


@volunteer_required
def task_detail(request, task_id):
    """
    View details of a specific task.
    """
    task = get_object_or_404(
        VolunteerTask, 
        id=task_id, 
        assigned_to=request.user
    )
    
    # Get task activities
    task_activities = VolunteerActivity.objects.filter(
        task=task
    ).order_by('-activity_date')
    
    # Handle task status updates
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'start_task':
            task.status = 'in_progress'
            task.start_date = timezone.now()
            task.save()
            
            # Log activity
            VolunteerActivity.objects.create(
                volunteer=request.user,
                activity_type='task_started',
                title=f'Started task: {task.title}',
                task=task,
                activity_date=timezone.now()
            )
            
            messages.success(request, 'Task started successfully!')
            
        elif action == 'complete_task':
            task.status = 'completed'
            task.completion_date = timezone.now()
            
            # Get actual hours from form
            actual_hours = request.POST.get('actual_hours')
            if actual_hours:
                try:
                    task.actual_hours = float(actual_hours)
                except ValueError:
                    pass
            
            task.save()
            
            # Log activity
            VolunteerActivity.objects.create(
                volunteer=request.user,
                activity_type='task_completed',
                title=f'Completed task: {task.title}',
                task=task,
                hours_logged=task.actual_hours,
                activity_date=timezone.now()
            )
            
            messages.success(request, 'Task completed successfully!')
            
        elif action == 'add_note':
            note = request.POST.get('note')
            if note:
                if task.notes:
                    task.notes += f"\n\n{timezone.now().strftime('%Y-%m-%d %H:%M')} - {note}"
                else:
                    task.notes = f"{timezone.now().strftime('%Y-%m-%d %H:%M')} - {note}"
                task.save()
                messages.success(request, 'Note added successfully!')
        
        return redirect('volunteer_dashboard:task_detail', task_id=task.id)
    
    context = {
        'task': task,
        'task_activities': task_activities,
    }
    
    return render(request, 'volunteer/task_detail.html', context)


@volunteer_required
def submit_report(request):
    """
    Submit activity reports.
    """
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        title = request.POST.get('title')
        description = request.POST.get('description')
        content = request.POST.get('content')
        hours_worked = request.POST.get('hours_worked')
        achievements = request.POST.get('achievements', '')
        challenges = request.POST.get('challenges', '')
        suggestions = request.POST.get('suggestions', '')
        action = request.POST.get('action', 'save_draft')
        
        # Validate required fields
        if not all([report_type, title, description, content]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'volunteer/submit_report.html', {
                'report_types': VolunteerReport.REPORT_TYPES
            })
        
        # Create the report
        report = VolunteerReport(
            volunteer=request.user,
            report_type=report_type,
            title=title,
            description=description,
            content=content,
            achievements=achievements,
            challenges=challenges,
            suggestions=suggestions
        )
        
        # Set hours worked if provided
        if hours_worked:
            try:
                report.hours_worked = float(hours_worked)
            except ValueError:
                pass
        
        # Set status based on action
        if action == 'submit':
            report.status = 'submitted'
            report.submitted_at = timezone.now()
        else:
            report.status = 'draft'
        
        report.save()
        
        # Log activity
        activity_type = 'report_submitted' if action == 'submit' else 'report_saved'
        VolunteerActivity.objects.create(
            volunteer=request.user,
            activity_type=activity_type,
            title=f'{"Submitted" if action == "submit" else "Saved"} report: {title}',
            activity_date=timezone.now()
        )
        
        messages.success(
            request, 
            f'Report {"submitted" if action == "submit" else "saved as draft"} successfully!'
        )
        return redirect('volunteer_dashboard:report_list')
    
    context = {
        'report_types': VolunteerReport.REPORT_TYPES
    }
    
    return render(request, 'volunteer/submit_report.html', context)


@volunteer_required
def report_list(request):
    """
    List volunteer's reports.
    """
    reports = VolunteerReport.objects.filter(
        volunteer=request.user
    ).order_by('-created_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    # Filter by type if requested
    type_filter = request.GET.get('type')
    if type_filter:
        reports = reports.filter(report_type=type_filter)
    
    # Pagination
    paginator = Paginator(reports, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': VolunteerReport.STATUS_CHOICES,
        'type_choices': VolunteerReport.REPORT_TYPES,
        'current_status': status_filter,
        'current_type': type_filter,
    }
    
    return render(request, 'volunteer/report_list.html', context)


@volunteer_required
def report_detail(request, report_id):
    """
    View details of a specific report.
    """
    report = get_object_or_404(
        VolunteerReport, 
        id=report_id, 
        volunteer=request.user
    )
    
    context = {
        'report': report,
    }
    
    return render(request, 'volunteer/report_detail.html', context)


@volunteer_required
def profile_update(request):
    """
    Update volunteer profile information.
    """
    volunteer = request.user
    
    if request.method == 'POST':
        # Update basic profile info
        volunteer.first_name = request.POST.get('first_name', volunteer.first_name)
        volunteer.last_name = request.POST.get('last_name', volunteer.last_name)
        volunteer.phone = request.POST.get('phone', volunteer.phone)
        volunteer.address = request.POST.get('address', volunteer.address)
        volunteer.bio = request.POST.get('bio', volunteer.bio)
        volunteer.save()
        
        # Handle skills update
        skills_data = request.POST.getlist('skills')
        proficiency_data = request.POST.getlist('proficiency')
        category_data = request.POST.getlist('category')
        
        if skills_data and proficiency_data:
            # Clear existing skills and add new ones
            VolunteerSkill.objects.filter(volunteer=volunteer).delete()
            
            for i, skill_name in enumerate(skills_data):
                if skill_name.strip():
                    try:
                        proficiency = int(proficiency_data[i]) if i < len(proficiency_data) else 3
                        category = category_data[i] if i < len(category_data) else ''
                        
                        VolunteerSkill.objects.create(
                            volunteer=volunteer,
                            skill_name=skill_name.strip(),
                            category=category.strip(),
                            proficiency_level=proficiency
                        )
                    except (ValueError, IndexError):
                        continue
        
        # Handle availability update
        availability_data = request.POST.get('availability')
        if availability_data:
            # This would typically be handled with JavaScript on the frontend
            # and submitted as JSON data for more complex scheduling
            pass
        
        # Log activity
        VolunteerActivity.objects.create(
            volunteer=volunteer,
            activity_type='profile_updated',
            title='Profile information updated',
            activity_date=timezone.now()
        )
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('volunteer_dashboard:profile_update')
    
    # Get current skills
    current_skills = VolunteerSkill.objects.filter(volunteer=volunteer)
    
    # Get current availability
    current_availability = VolunteerAvailability.objects.filter(
        volunteer=volunteer,
        is_active=True
    ).order_by('day_of_week', 'start_time')
    
    context = {
        'volunteer': volunteer,
        'current_skills': current_skills,
        'current_availability': current_availability,
        'proficiency_levels': VolunteerSkill.PROFICIENCY_LEVELS,
        'days_of_week': VolunteerAvailability.DAYS_OF_WEEK,
    }
    
    return render(request, 'volunteer/profile_update.html', context)


@volunteer_required
def activity_log(request):
    """
    View volunteer's activity log.
    """
    activities = VolunteerActivity.objects.filter(
        volunteer=request.user
    ).order_by('-activity_date')
    
    # Filter by activity type if requested
    type_filter = request.GET.get('type')
    if type_filter:
        activities = activities.filter(activity_type=type_filter)
    
    # Filter by date range if requested
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            activities = activities.filter(activity_date__date__gte=from_date)
        except ValueError:
            pass
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            activities = activities.filter(activity_date__date__lte=to_date)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(activities, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'activity_types': VolunteerActivity.ACTIVITY_TYPES,
        'current_type': type_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'volunteer/activity_log.html', context)


@volunteer_required
@require_http_methods(["POST"])
def log_hours(request):
    """
    Log volunteer hours (AJAX endpoint).
    """
    hours = request.POST.get('hours')
    description = request.POST.get('description', 'Manual hours entry')
    activity_date = request.POST.get('date')
    
    try:
        hours_float = float(hours)
        if hours_float <= 0:
            return JsonResponse({'success': False, 'error': 'Hours must be greater than 0'})
        
        # Parse date
        if activity_date:
            activity_date = datetime.strptime(activity_date, '%Y-%m-%d')
        else:
            activity_date = timezone.now()
        
        # Create activity
        VolunteerActivity.objects.create(
            volunteer=request.user,
            activity_type='hours_logged',
            title='Manual hours entry',
            description=description,
            hours_logged=hours_float,
            activity_date=activity_date
        )
        
        return JsonResponse({'success': True, 'message': 'Hours logged successfully'})
        
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid hours value'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@volunteer_required
def dashboard_stats_api(request):
    """
    API endpoint for dashboard statistics (AJAX).
    """
    volunteer = request.user
    
    # Task statistics
    my_tasks = VolunteerTask.objects.filter(assigned_to=volunteer)
    task_stats = {
        'pending': my_tasks.filter(status='pending').count(),
        'in_progress': my_tasks.filter(status='in_progress').count(),
        'completed': my_tasks.filter(status='completed').count(),
        'overdue': my_tasks.filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        ).count(),
    }
    
    # Hours this week
    week_start = timezone.now() - timedelta(days=timezone.now().weekday())
    week_hours = VolunteerActivity.objects.filter(
        volunteer=volunteer,
        activity_date__gte=week_start,
        hours_logged__isnull=False
    ).aggregate(total=Sum('hours_logged'))['total'] or 0
    
    # Report statistics
    my_reports = VolunteerReport.objects.filter(volunteer=volunteer)
    report_stats = {
        'draft': my_reports.filter(status='draft').count(),
        'submitted': my_reports.filter(status='submitted').count(),
        'approved': my_reports.filter(status='approved').count(),
    }
    
    data = {
        'task_stats': task_stats,
        'week_hours': float(week_hours),
        'report_stats': report_stats,
        'timestamp': timezone.now().isoformat()
    }
    
    return JsonResponse(data)


@volunteer_required
def events_list(request):
    """
    List of available events for volunteers.
    """
    events = VolunteerEvent.objects.filter(
        status='upcoming',
        start_date__gte=timezone.now()
    ).order_by('start_date')
    
    # Filter by event type if requested
    type_filter = request.GET.get('type')
    if type_filter:
        events = events.filter(event_type=type_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(events, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'event_types': VolunteerEvent.EVENT_TYPES,
        'current_type': type_filter,
        'search_query': search_query,
    }
    
    return render(request, 'volunteer/events_list.html', context)


@volunteer_required
def event_detail(request, event_id):
    """
    View details of a specific event.
    """
    event = get_object_or_404(VolunteerEvent, id=event_id)
    volunteer = request.user
    
    # Check if volunteer is already registered
    is_registered = VolunteerEventRegistration.objects.filter(
        volunteer=volunteer,
        event=event
    ).exists()
    
    # Handle event registration
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'register' and not is_registered and event.can_register:
            registration = VolunteerEventRegistration.objects.create(
                volunteer=volunteer,
                event=event,
                emergency_contact=request.POST.get('emergency_contact', ''),
                emergency_phone=request.POST.get('emergency_phone', ''),
                dietary_restrictions=request.POST.get('dietary_restrictions', ''),
                special_requirements=request.POST.get('special_requirements', '')
            )
            
            # Log activity
            VolunteerActivity.objects.create(
                volunteer=volunteer,
                activity_type='event_participated',
                title=f'Registered for event: {event.title}',
                activity_date=timezone.now()
            )
            
            messages.success(request, f'Successfully registered for {event.title}!')
            is_registered = True
            
        elif action == 'unregister' and is_registered:
            VolunteerEventRegistration.objects.filter(
                volunteer=volunteer,
                event=event
            ).delete()
            
            messages.success(request, f'Successfully unregistered from {event.title}!')
            is_registered = False
        
        return redirect('volunteer_dashboard:event_detail', event_id=event.id)
    
    # Get registration if exists
    registration = None
    if is_registered:
        registration = VolunteerEventRegistration.objects.get(
            volunteer=volunteer,
            event=event
        )
    
    context = {
        'event': event,
        'is_registered': is_registered,
        'registration': registration,
    }
    
    return render(request, 'volunteer/event_detail.html', context)


@volunteer_required
def my_events(request):
    """
    List of events the volunteer is registered for.
    """
    volunteer = request.user
    registrations = VolunteerEventRegistration.objects.filter(
        volunteer=volunteer
    ).order_by('-registration_date')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        registrations = registrations.filter(attendance_status=status_filter)
    
    # Pagination
    paginator = Paginator(registrations, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': VolunteerEventRegistration.ATTENDANCE_CHOICES,
        'current_status': status_filter,
    }
    
    return render(request, 'volunteer/my_events.html', context)


@volunteer_required
def resources_list(request):
    """
    List of available resources for volunteers.
    """
    resources = VolunteerResource.objects.filter(
        is_active=True,
        access_level__in=['public', 'volunteer']
    ).order_by('-is_featured', '-last_updated')
    
    # Filter by resource type if requested
    type_filter = request.GET.get('type')
    if type_filter:
        resources = resources.filter(resource_type=type_filter)
    
    # Filter by category if requested
    category_filter = request.GET.get('category')
    if category_filter:
        resources = resources.filter(category__icontains=category_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        resources = resources.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Get categories for filter
    categories = VolunteerResource.objects.filter(
        is_active=True,
        access_level__in=['public', 'volunteer']
    ).values_list('category', flat=True).distinct()
    categories = [cat for cat in categories if cat]
    
    # Pagination
    paginator = Paginator(resources, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'resource_types': VolunteerResource.RESOURCE_TYPES,
        'categories': categories,
        'current_type': type_filter,
        'current_category': category_filter,
        'search_query': search_query,
    }
    
    return render(request, 'volunteer/resources_list.html', context)


@volunteer_required
def resource_download(request, resource_id):
    """
    Handle resource download and tracking.
    """
    resource = get_object_or_404(VolunteerResource, id=resource_id, is_active=True)
    volunteer = request.user
    
    # Check access permissions
    if resource.access_level == 'coordinator' and volunteer.role != 'coordinator':
        messages.error(request, 'You do not have permission to access this resource.')
        return redirect('volunteer_dashboard:resources_list')
    
    if resource.access_level == 'admin' and volunteer.role != 'admin':
        messages.error(request, 'You do not have permission to access this resource.')
        return redirect('volunteer_dashboard:resources_list')
    
    # Track resource access
    VolunteerResourceAccess.objects.create(
        volunteer=volunteer,
        resource=resource,
        access_type='download',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Increment download count
    resource.increment_download_count()
    
    # Log activity
    VolunteerActivity.objects.create(
        volunteer=volunteer,
        activity_type='resource_downloaded',
        title=f'Downloaded resource: {resource.title}',
        activity_date=timezone.now()
    )
    
    if resource.file_url:
        return redirect(resource.file_url)
    else:
        messages.error(request, 'Resource file not available.')
        return redirect('volunteer_dashboard:resources_list')


@volunteer_required
def reports_dashboard(request):
    """
    Reports dashboard showing NGO reports and statistics.
    """
    volunteer = request.user
    
    # Sample report data - in a real app, this would come from a separate reports app
    reports = [
        {
            'title': 'Quarterly Impact Report - Q2 2025',
            'date': 'Published: 15 July, 2025',
            'description': 'This comprehensive report details NEXAS\'s activities and impact during the second quarter of 2025.',
            'file_url': 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
            'filename': 'NEXAS_Q2_2025_Report.pdf'
        },
        {
            'title': 'Annual Financial Report 2024',
            'date': 'Published: 28 February, 2025',
            'description': 'This report provides a comprehensive financial overview of NEXAS NGO for the fiscal year 2024.',
            'file_url': 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
            'filename': 'NEXAS_Financial_Report_2024.pdf'
        },
        {
            'title': 'Community Impact Assessment 2024-2025',
            'date': 'Published: 10 June, 2025',
            'description': 'This detailed assessment measures the long-term impact of NEXAS programs across the communities we serve.',
            'file_url': 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
            'filename': 'NEXAS_Impact_Assessment_2025.pdf'
        }
    ]
    
    context = {
        'reports': reports,
    }
    
    return render(request, 'volunteer/reports_dashboard.html', context)
