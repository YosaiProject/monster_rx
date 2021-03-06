def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('launchpad', '/launchpad')
    config.add_route('request_rx', '/request_rx')
    config.add_route('rx_portal', '/rx_portal')
    config.add_route('pending_rx', '/pending_rx')
    config.add_route('write_rx', '/write_rx')
    config.add_route('write_rx_form', '/write_rx_form')
