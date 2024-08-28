def breadcrumbs(request):
    breadcrumbs = []
    path = request.path.strip('/').split('/')
    
    for i in range(len(path)):
        url = '/' + '/'.join(path[:i+1]) + '/'
        breadcrumbs.append((path[i].capitalize(), url))

    return {
        'breadcrumbs': breadcrumbs
    }