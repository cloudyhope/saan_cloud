"""Line icons for the admin sidebar, stored in AdminMenu.active_icon / deactive_icon.

The sidebar already renders whatever these two fields hold (a URL or a data URI). Icons are
24px outline glyphs with one stroke weight; the active variant is white for the highlighted
item and the inactive variant is a muted blue-grey that reads on the dark sidebar.
"""
from urllib.parse import quote

ACTIVE_COLOR = '#ffffff'
INACTIVE_COLOR = '#9fb0cc'

PATHS = {
    'grid': 'M4 4h6.5v6.5H4zM13.5 4H20v6.5h-6.5zM4 13.5h6.5V20H4zM13.5 13.5H20V20h-6.5z',
    'users': 'M15.5 19v-1.5a3.5 3.5 0 0 0-3.5-3.5H7a3.5 3.5 0 0 0-3.5 3.5V19M9.5 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6'
             'M20.5 19v-1.5a3.5 3.5 0 0 0-2.6-3.4M15 5.1a3 3 0 0 1 0 5.8',
    'user-plus': 'M14 19v-1.5a3.5 3.5 0 0 0-3.5-3.5h-4A3.5 3.5 0 0 0 3 17.5V19M8.5 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6'
                 'M19 8v6M16 11h6',
    'user-check': 'M14 19v-1.5a3.5 3.5 0 0 0-3.5-3.5h-4A3.5 3.5 0 0 0 3 17.5V19M8.5 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6'
                  'm7.5 1 2 2 4-4',
    'briefcase': 'M4 8h16v11H4zM9 8V5.5h6V8M4 13h16',
    'id-card': 'M3 6h18v12H3zM8.5 12a2 2 0 1 0 0-4 2 2 0 0 0 0 4M5.5 16a3 3 0 0 1 6 0M14 10h4M14 14h3',
    'square-plus': 'M4 4h16v16H4zM12 8v8M8 12h8',
    'elevator': 'M5 3h14v18H5zM12 3v18M7.5 10 9 8l1.5 2M13.5 14l1.5 2 1.5-2',
    'building': 'M6 21V4h9v17M15 9h4v12M3 21h18M9 8h3M9 12h3M9 16h3',
    'buildings': 'M3 21h18M5 21V9h6v12M13 21V4h6v17M7.5 13h1M7.5 17h1M15.5 8h1M15.5 12h1M15.5 16h1',
    'clipboard-check': 'M9 3.5h6v3H9zM9 5H6v15.5h12V5h-3M9.5 13l2 2 3.5-3.5',
    'clipboard-clock': 'M9 3.5h6v3H9zM9 5H6v15.5h12V5h-3M12 10.5v3.2l2 1.3',
    'circle-check': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18M8.5 12.5l2.5 2.5 4.5-5',
    'list': 'M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01',
    'survey': 'M9 3.5h6v3H9zM9 5H6v15.5h12V5h-3M9 11h6M9 15h4',
    'eye': 'M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6',
    'calendar': 'M4 6h16v14H4zM4 10h16M8 3v4M16 3v4',
    'calendar-plus': 'M4 6h16v14H4zM4 10h16M8 3v4M16 3v4M12 13v5M9.5 15.5h5',
    'headset': 'M4 14v-2a8 8 0 0 1 16 0v2M4 14h3v5H5a1 1 0 0 1-1-1zM20 14h-3v5h2a1 1 0 0 0 1-1zM17 19c0 1.4-1.8 2-4 2',
    'message-plus': 'M4 5h16v11H9l-5 4zM12 8v5M9.5 10.5h5',
    'messages': 'M4 5h16v11H9l-5 4zM8 9h8M8 12.5h5',
    'package': 'M12 3l8 4.5v9L12 21l-8-4.5v-9zM4 7.5l8 4.5 8-4.5M12 12v9',
    'boxes': 'M3 13h8v8H3zM13 13h8v8h-8zM8 3h8v8H8z',
    'shield-check': 'M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6zM8.5 12l2.5 2.5 4.5-4.5',
    'bell': 'M6 16v-5a6 6 0 0 1 12 0v5l2 2H4zM10 20.5a2 2 0 0 0 4 0',
    'store': 'M4 10v10h16V10M3.5 6 5 3.5h14L20.5 6v2a2.8 2.8 0 0 1-5.6 0 2.8 2.8 0 0 1-5.8 0A2.8 2.8 0 0 1 3.5 8zM10 20v-5h4v5',
    'image': 'M4 4h16v16H4zM4 16l4.5-4.5L13 16l2.5-2.5L20 18M15.5 8.5h.01',
    'folder': 'M3 6h6l2 2h10v11H3z',
    'upload': 'M12 15V4M7.5 8.5 12 4l4.5 4.5M4 15v5h16v-5',
    'wallet': 'M4 7h15v12H4zM4 7l11-3v3M15 11.5h4v4h-4z',
    'card': 'M3 6h18v12H3zM3 10h18M7 15h3',
    'camera': 'M4 8h3.5L9 5.5h6L16.5 8H20v11H4zM12 16.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7',
    'gauge': 'M4.5 17a8.5 8.5 0 1 1 15 0M12 13.5l3.5-4.5M12 15a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3',
    'dot': 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6',
    'user-star': 'M14 19v-1.5a3.5 3.5 0 0 0-3.5-3.5h-4A3.5 3.5 0 0 0 3 17.5V19M8.5 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6'
                 'M18 6l.9 1.9 2.1.3-1.5 1.5.4 2.1-1.9-1-1.9 1 .4-2.1L15 8.2l2.1-.3z',
    'package-request': 'M12 3l8 4.5v5M4 7.5v9L12 21l3-1.7M4 7.5l8 4.5 8-4.5M12 12v9M18 15v6M15 18h6',
    'sliders': 'M5 21v-7M5 10V3M12 21v-9M12 8V3M19 21v-5M19 12V3M2.5 14h5M9.5 8h5M16.5 16h5',
}

# Exact destinations (lower-case, no trailing slash) → icon.
ROUTES = {
    '/dashboard': 'grid', '/notifications': 'bell', '/priority': 'gauge', '/service-cases': 'shield-check', '/storemng/listall': 'store',
    '/usermanagement/list': 'users', '/usermanagement/add': 'user-plus', '/usermanagement/assignpromoter': 'user-check',
    '/customermanagement/list': 'id-card', '/customermanagement/create': 'square-plus',
    '/elevatormanagement/buildinglist': 'building', '/elevatormanagement/crearebuilding': 'square-plus',
    '/elevatormanagement/groupbuildinglist': 'buildings', '/elevatormanagement/elevatorlist': 'elevator',
    '/visitmanagment/lists': 'list', '/visitmanagment/notcompeletevisits': 'clipboard-clock',
    '/visitmanagment/completevisited': 'clipboard-check', '/visitmanagment/acceptedvisits': 'circle-check',
    '/suveymanagment/lists': 'list', '/surveymanagment/notcompeletesurvey': 'clipboard-clock',
    '/suveymanagment/completesurvey': 'clipboard-check', '/surveymanagment/acceptedsurvey': 'circle-check',
    '/supervisionmanagment/lists': 'list', '/supervisionmanagment/notcompeletesupervision': 'clipboard-clock',
    '/supervisionmanagment/completesupervision': 'clipboard-check', '/supervisionmanagment/acceptedsupervision': 'circle-check',
    '/actionplan/newaction': 'calendar-plus', '/actionplan/listactionplan': 'list',
    '/ticket/newticket': 'message-plus', '/ticket/ticketlist': 'messages',
    '/warehouse/create': 'package', '/warehouse/warelist': 'boxes', '/warehouse/part-requests': 'package-request',
    '/visitmanagment/visit-types': 'sliders', '/assignment': 'user-star',
    '/medialist/list': 'image', '/medialist/create': 'square-plus',
    '/filemanagement/filelist': 'folder', '/filemanagement/uploadfile': 'upload',
    '/walletmanagment/manageaccount': 'wallet', '/walletmanagment/rechargewallet': 'card',
}
# A menu group takes the icon of its section (the first path segment).
SECTIONS = {
    'dashboard': 'grid', 'usermanagement': 'users', 'customermanagement': 'briefcase', 'elevatormanagement': 'elevator',
    'visitmanagment': 'clipboard-check', 'suveymanagment': 'survey', 'surveymanagment': 'survey',
    'supervisionmanagment': 'eye', 'actionplan': 'calendar', 'ticket': 'headset', 'warehouse': 'package',
    'medialist': 'image', 'filemanagement': 'folder', 'walletmanagment': 'wallet', 'pic': 'camera',
    'storemng': 'store', 'service-cases': 'shield-check', 'notifications': 'bell', 'priority': 'gauge',
}


def canonical(route):
    return (route or '').split('?')[0].strip().rstrip('/').lower() or '/'


def icon_key(route, is_group=False):
    path = canonical(route)
    section = path.strip('/').split('/')[0]
    if is_group:
        return SECTIONS.get(section, 'folder')
    return ROUTES.get(path) or SECTIONS.get(section) or 'dot'


def data_uri(key, color):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
           f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="{PATHS[key]}"/></svg>')
    return 'data:image/svg+xml;charset=utf-8,' + quote(svg, safe='')


def icons_for(route, is_group=False):
    """Return (active_icon, deactive_icon) for one menu row."""
    key = icon_key(route, is_group)
    return data_uri(key, ACTIVE_COLOR), data_uri(key, INACTIVE_COLOR)
