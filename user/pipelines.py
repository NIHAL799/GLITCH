def save_user_details(strategy, details, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}
    
    fields = {
        'username': details.get('username'),
        'email': details.get('email'),
        'first_name': details.get('first_name'),
        'last_name': details.get('last_name', 'Unknown'),
    }
    return {'is_new': True, 'user': strategy.create_user(**fields)}