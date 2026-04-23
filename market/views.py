from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import Http404
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_POST

from .models import SellerProfile, ProductCategory, Product
from .forms import SellerApplicationForm, ProductForm, SellerReviewForm


def _is_leader(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or getattr(user, 'is_admin', False) or user.is_staff:
        return True
    try:
        if not user.leader_profile.is_active:
            return False
        return (user.leader_profile.permissions.can_manage_users
                or user.leader_profile.permissions.can_verify_users
                or user.leader_profile.role in ('president', 'vice_president', 'secretary'))
    except Exception:
        return False


def market_home(request):
    products = Product.objects.filter(
        is_available=True, seller__status='approved', seller__active=True,
    ).select_related('seller', 'category')

    q = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    city = request.GET.get('city', '').strip()
    free_delivery = request.GET.get('free') == '1'

    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q) |
                                   Q(seller__business_name__icontains=q))
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if city:
        products = products.filter(city=city)
    if free_delivery:
        products = products.filter(free_delivery_korea=True)

    paginator = Paginator(products, 24)
    page = paginator.get_page(request.GET.get('page'))

    categories = ProductCategory.objects.filter(active=True).annotate(
        count=Count('products', filter=Q(
            products__is_available=True,
            products__seller__status='approved',
        ))
    )

    featured = Product.objects.filter(
        is_available=True, featured=True,
        seller__status='approved', seller__active=True,
    ).select_related('seller')[:6]

    return render(request, 'market/home.html', {
        'products': page, 'categories': categories, 'featured': featured,
        'q': q, 'category_slug': category_slug, 'city': city, 'free_delivery': free_delivery,
    })


def category_detail(request, slug):
    category = get_object_or_404(ProductCategory, slug=slug, active=True)
    products = Product.objects.filter(
        is_available=True, category=category,
        seller__status='approved', seller__active=True,
    ).select_related('seller')
    paginator = Paginator(products, 24)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'market/category_detail.html', {
        'category': category, 'products': page,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('seller', 'category'),
        slug=slug,
    )
    is_owner = request.user.is_authenticated and request.user == product.seller.user
    is_staff_viewer = _is_leader(request.user)

    if not product.is_available or product.seller.status != 'approved':
        if not (is_owner or is_staff_viewer):
            raise Http404()

    # Count one view per session per product (refreshes don't inflate the number).
    # The seller's own visits and staff visits are also NOT counted.
    if not (is_owner or is_staff_viewer):
        viewed_key = f'viewed_product_{product.pk}'
        if not request.session.get(viewed_key):
            request.session[viewed_key] = True
            Product.objects.filter(pk=product.pk).update(
                views_count=product.views_count + 1
            )

    related = Product.objects.filter(
        is_available=True, seller__status='approved',
        category=product.category,
    ).exclude(pk=product.pk).select_related('seller')[:4]

    other_by_seller = Product.objects.filter(
        is_available=True, seller=product.seller,
    ).exclude(pk=product.pk)[:4]

    return render(request, 'market/product_detail.html', {
        'product': product, 'related': related, 'other_by_seller': other_by_seller,
    })


def seller_detail(request, slug):
    seller = get_object_or_404(SellerProfile, slug=slug, status='approved', active=True)
    products = Product.objects.filter(seller=seller, is_available=True).select_related('category')
    return render(request, 'market/seller_detail.html', {
        'seller': seller, 'products': products,
    })


@login_required
def apply_to_sell(request):
    existing = SellerProfile.objects.filter(user=request.user).first()
    if existing:
        return redirect('market:my_application')

    if request.method == 'POST':
        form = SellerApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            sp = form.save(commit=False)
            sp.user = request.user
            sp.save()
            messages.success(request,
                'Your seller application has been submitted. A KCK leader will review it soon.')
            return redirect('market:my_application')
    else:
        form = SellerApplicationForm(initial={
            'business_name': request.user.get_full_name() or request.user.username,
            'phone': getattr(request.user, 'phone', ''),
            'whatsapp_number': getattr(request.user, 'phone', ''),
            'city': getattr(request.user, 'city', ''),
            'email_contact': request.user.email,
        })
    return render(request, 'market/apply.html', {'form': form})


@login_required
def my_application(request):
    sp = getattr(request.user, 'seller_profile', None)
    if not sp:
        return redirect('market:apply')
    # Expose under both 'seller' and 'application' for template compatibility
    return render(request, 'market/my_application.html', {'seller': sp, 'application': sp})


@login_required
def seller_dashboard(request):
    sp = getattr(request.user, 'seller_profile', None)
    if not sp:
        return redirect('market:apply')
    if sp.status != 'approved':
        return redirect('market:my_application')
    products = sp.products.all().order_by('-created_at')
    return render(request, 'market/dashboard.html', {
        'seller': sp, 'products': products,
        'available_count': products.filter(is_available=True).count(),
        'total_views': sum(p.views_count for p in products),
    })


@login_required
def product_create(request):
    sp = getattr(request.user, 'seller_profile', None)
    if not sp or sp.status != 'approved':
        messages.error(request, 'You must be an approved seller to list products.')
        return redirect('market:my_application')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = sp
            product.save()
            messages.success(request, f'"{product.name}" has been listed. It is now live on the market.')
            return redirect('market:dashboard')
    else:
        form = ProductForm()
    return render(request, 'market/product_form.html', {'form': form, 'action': 'Create'})


@login_required
def product_edit(request, slug):
    product = get_object_or_404(Product, slug=slug, seller__user=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{product.name}" updated.')
            return redirect('market:dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'market/product_form.html', {
        'form': form, 'action': 'Edit', 'product': product,
    })


@login_required
@require_POST
def product_delete(request, slug):
    product = get_object_or_404(Product, slug=slug, seller__user=request.user)
    product.delete()
    messages.success(request, 'Product deleted.')
    return redirect('market:dashboard')


@login_required
@require_POST
def product_toggle(request, slug):
    """Quickly toggle a product's availability on/off from the dashboard."""
    product = get_object_or_404(Product, slug=slug, seller__user=request.user)
    product.is_available = not product.is_available
    product.save(update_fields=['is_available', 'updated_at'])
    state = 'available' if product.is_available else 'hidden'
    messages.success(request, f'"{product.name}" is now {state}.')
    return redirect('market:dashboard')


@login_required
@user_passes_test(_is_leader)
def leader_queue(request):
    pending_qs = SellerProfile.objects.filter(status='pending').order_by('applied_at')
    approved = SellerProfile.objects.filter(status='approved').count()
    rejected = SellerProfile.objects.filter(status='rejected').count()
    suspended = SellerProfile.objects.filter(status='suspended').count()
    return render(request, 'market/leader_queue.html', {
        # Names matching the current template
        'pending_apps': pending_qs,
        'pending_count': pending_qs.count(),
        'approved_total': approved,
        'rejected_total': rejected,
        'suspended_total': suspended,
        # Backward-compatible aliases
        'pending': pending_qs,
        'approved_count': approved,
        'rejected_count': rejected,
    })


@login_required
@user_passes_test(_is_leader)
def leader_review(request, pk):
    seller = get_object_or_404(SellerProfile, pk=pk)
    if request.method == 'POST':
        form = SellerReviewForm(request.POST)
        if form.is_valid():
            seller.status = form.cleaned_data['decision']
            seller.review_notes = form.cleaned_data['notes']
            seller.reviewed_at = timezone.now()
            seller.reviewed_by = request.user
            seller.save()
            action = 'approved' if seller.status == 'approved' else 'rejected'
            messages.success(request,
                f'Seller "{seller.business_name}" has been {action}.')
            return redirect('market:leader_queue')
    else:
        form = SellerReviewForm(initial={'decision': 'approved'})
    return render(request, 'market/leader_review.html', {
        'seller': seller, 'application': seller, 'form': form,
    })


@login_required
@user_passes_test(_is_leader)
def leader_all_sellers(request):
    status = request.GET.get('status', 'approved')
    sellers = SellerProfile.objects.all().select_related('user', 'reviewed_by')
    valid_statuses = {c[0] for c in SellerProfile._meta.get_field('status').choices}
    if status in valid_statuses:
        sellers = sellers.filter(status=status)
    return render(request, 'market/leader_all_sellers.html', {
        'sellers': sellers, 'status': status,
    })
