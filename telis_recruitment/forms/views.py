"""Views for form builder"""
import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify

from .models import Form, FormField, FormSubmission
from leads.models import Lead

logger = logging.getLogger(__name__)


# ===== Form Management Views =====

@staff_member_required
def form_list(request):
    """List all forms"""
    forms = Form.objects.all()
    return render(request, 'forms/list.html', {
        'forms': forms,
    })


@staff_member_required
def form_create(request):
    """Create a new form"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if not name:
            messages.error(request, 'Form name is required')
            return redirect('forms:list')
        
        # Generate unique slug
        slug = slugify(name)
        base_slug = slug
        counter = 1
        while Form.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        form = Form.objects.create(
            name=name,
            slug=slug,
            description=description,
            created_by=request.user
        )
        
        messages.success(request, f'Form "{name}" created successfully')
        return redirect('forms:builder', slug=form.slug)
    
    return render(request, 'forms/create.html')


@staff_member_required
def form_detail(request, slug):
    """View form details"""
    form = get_object_or_404(Form, slug=slug)
    return render(request, 'forms/detail.html', {
        'form': form,
    })


@staff_member_required
def form_edit(request, slug):
    """Edit form settings"""
    form = get_object_or_404(Form, slug=slug)
    
    if request.method == 'POST':
        form.name = request.POST.get('name', form.name)
        form.description = request.POST.get('description', '')
        form.status = request.POST.get('status', 'draft')
        form.submit_button_text = request.POST.get('submit_button_text', 'Submit')
        form.success_message = request.POST.get('success_message', 'Thank you!')
        form.redirect_url = request.POST.get('redirect_url', '')
        form.save_to_leads = request.POST.get('save_to_leads') == 'on'
        form.send_email_notification = request.POST.get('send_email_notification') == 'on'
        form.notification_email = request.POST.get('notification_email', '')
        
        form.save()
        messages.success(request, 'Form settings updated')
        return redirect('forms:detail', slug=slug)
    
    return render(request, 'forms/edit.html', {
        'form': form,
    })


@staff_member_required
@require_POST
def form_delete(request, slug):
    """Delete a form"""
    form = get_object_or_404(Form, slug=slug)
    form_name = form.name
    form.delete()
    
    messages.success(request, f'Form "{form_name}" deleted successfully')
    return redirect('forms:list')


# ===== Form Builder View =====

@staff_member_required
def form_builder(request, slug):
    """Visual form builder interface"""
    form = get_object_or_404(Form, slug=slug)
    fields = form.fields.all()
    
    return render(request, 'forms/builder.html', {
        'form': form,
        'fields': fields,
    })


# ===== Form Preview =====

@staff_member_required
def form_preview(request, slug):
    """Preview the form"""
    form = get_object_or_404(Form, slug=slug)
    fields = form.fields.all()
    
    return render(request, 'forms/preview.html', {
        'form': form,
        'fields': fields,
    })


# ===== Submissions =====

@staff_member_required
def form_submissions(request, slug):
    """View form submissions"""
    form = get_object_or_404(Form, slug=slug)
    submissions = form.submissions.all()
    
    return render(request, 'forms/submissions.html', {
        'form': form,
        'submissions': submissions,
    })


@staff_member_required
def submission_detail(request, slug, submission_id):
    """View individual submission"""
    form = get_object_or_404(Form, slug=slug)
    submission = get_object_or_404(FormSubmission, id=submission_id, form=form)
    
    return render(request, 'forms/submission_detail.html', {
        'form': form,
        'submission': submission,
    })


# ===== API Endpoints =====

@staff_member_required
@require_GET
def api_get_fields(request, slug):
    """Get form fields as JSON"""
    form = get_object_or_404(Form, slug=slug)
    fields = form.fields.all()
    
    fields_data = []
    for field in fields:
        fields_data.append({
            'id': field.id,
            'label': field.label,
            'field_type': field.field_type,
            'field_name': field.field_name,
            'placeholder': field.placeholder,
            'help_text': field.help_text,
            'options': field.options,
            'required': field.required,
            'min_length': field.min_length,
            'max_length': field.max_length,
            'pattern': field.pattern,
            'allowed_file_types': field.allowed_file_types,
            'max_file_size': field.max_file_size,
            'order': field.order,
            'width': field.width,
        })
    
    return JsonResponse({
        'success': True,
        'fields': fields_data
    })


@staff_member_required
@require_POST
def api_save_fields(request, slug):
    """Save form fields from builder"""
    try:
        form = get_object_or_404(Form, slug=slug)
        data = json.loads(request.body)
        fields_data = data.get('fields', [])
        
        # Delete existing fields
        form.fields.all().delete()
        
        # Create new fields
        for field_data in fields_data:
            FormField.objects.create(
                form=form,
                label=field_data.get('label', 'Untitled Field'),
                field_type=field_data.get('field_type', 'text'),
                field_name=field_data.get('field_name', slugify(field_data.get('label', 'field'))),
                placeholder=field_data.get('placeholder', ''),
                help_text=field_data.get('help_text', ''),
                options=field_data.get('options', []),
                required=field_data.get('required', False),
                min_length=field_data.get('min_length'),
                max_length=field_data.get('max_length'),
                pattern=field_data.get('pattern', ''),
                allowed_file_types=field_data.get('allowed_file_types', ''),
                max_file_size=field_data.get('max_file_size'),
                order=field_data.get('order', 0),
                width=field_data.get('width', 'full'),
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Saved {len(fields_data)} fields'
        })
    
    except Exception as e:
        logger.error(f"Error saving fields: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_POST
def api_submit_form(request, slug):
    """Handle form submission (public endpoint with CSRF protection)"""
    try:
        form = get_object_or_404(Form, slug=slug, status='published')
        
        # Parse form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = dict(request.POST)
        
        # Create submission
        submission = FormSubmission.objects.create(
            form=form,
            data=data,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Create lead if configured
        if form.save_to_leads:
            try:
                # Validate required fields
                name = data.get('name', '').strip()
                email = data.get('email', '').strip()
                
                if not name:
                    logger.warning("Cannot create lead: name is missing")
                else:
                    lead_data = {
                        'name': name,
                        'email': email if email else None,
                        'telefon': data.get('phone') or data.get('telefon'),
                        'source': 'form',
                        'form_name': form.name,
                    }
                    
                    lead = Lead.objects.create(**lead_data)
                    submission.lead_created = True
                    submission.lead_id = lead.id
                    submission.save()
                    
                    logger.info(f"Created lead {lead.id} from form submission")
            except Exception as e:
                logger.error(f"Error creating lead from submission: {e}")
        
        # Send notification email if configured
        if form.send_email_notification and form.notification_email:
            # Email notification can be implemented using Django's email system
            # For now, just log the notification
            logger.info(f"Form submission received - notification configured for {form.notification_email}")
        
        return JsonResponse({
            'success': True,
            'message': form.success_message,
            'redirect_url': form.redirect_url
        })
    
    except Exception as e:
        logger.error(f"Error processing form submission: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error processing form submission'
        }, status=500)
