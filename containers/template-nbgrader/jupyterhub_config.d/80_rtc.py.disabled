# configure Jupyter RTC

c = get_config()

# First 28 characters of room names have to be unique to each room.
# Room names have to be URL save (no spaces aso.).

public_rtc_rooms = ['public-collab-1', 'public-collab-2']

private_rtc_rooms = [
    {
        'name': 'private-collab-1',
        'users': ['user1', 'user2'],
        'groups': []
    },
    {
        'name': 'private-collab-2',
        'users': ['user1', 'user3'],
        'groups': []
    }
]

# create rooms
with open('/opt/install/rtc_config.py') as f:
    exec(f.read())
 
