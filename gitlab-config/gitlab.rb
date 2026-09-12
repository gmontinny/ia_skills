external_url 'http://192.168.15.4'
gitlab_rails['gitlab_shell_ssh_port'] = 2222
gitlab_rails['initial_root_password'] = 'Xk9mP2vL7nQ4wRst'
gitlab_rails['initial_shared_runners_registration_token'] = 'initial-runner-token'
gitlab_rails['smtp_enable'] = false
puma['worker_processes'] = 2
sidekiq['concurrency'] = 10
postgresql['shared_buffers'] = '256MB'
gitlab_rails['backup_keep_time'] = 604800
