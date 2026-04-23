from django.shortcuts import render, get_object_or_404
from collections import OrderedDict
from .models import Leader, LEADER_ROLE_CHOICES


ROLE_ORDER = ['president', 'vice_president', 'secretary', 'treasurer', 'welfare', 'committee']


def leaders_list(request):
    leaders = Leader.objects.filter(is_active=True).select_related('user').order_by('sort_order', 'role')

    role_labels = dict(LEADER_ROLE_CHOICES)
    grouped = OrderedDict()
    for role_key in ROLE_ORDER:
        grouped[role_key] = {
            'label': role_labels.get(role_key, role_key.title()),
            'leaders': [],
        }

    for leader in leaders:
        if leader.role in grouped:
            grouped[leader.role]['leaders'].append(leader)
        else:
            grouped.setdefault(leader.role, {
                'label': role_labels.get(leader.role, leader.role.title()),
                'leaders': [],
            })['leaders'].append(leader)

    grouped = OrderedDict((k, v) for k, v in grouped.items() if v['leaders'])

    context = {
        'grouped_leaders': grouped,
        'leaders': leaders,
    }
    return render(request, 'leaders/leader_list.html', context)


def leader_detail(request, pk):
    leader = get_object_or_404(Leader.objects.select_related('user'), pk=pk, is_active=True)
    return render(request, 'leaders/leader_detail.html', {'leader': leader})
