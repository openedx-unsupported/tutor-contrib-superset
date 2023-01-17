from glob import glob
import os
import pkg_resources

from tutor import hooks

from .__about__ import __version__


########################################
# CONFIGURATION
########################################

hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        # Add your new settings that have default values here.
        # Each new setting is a pair: (setting_name, default_value).
        # Prefix your setting names with 'SUPERSET_'.
        ("SUPERSET_VERSION", __version__),
        ("SUPERSET_TAG", "latest-dev"),
        ("SUPERSET_HOST", "{{ LMS_HOST }}"),
        ("SUPERSET_PORT", "8088"),
        # TODO: use our mysql database instead?
        ("SUPERSET_DB_DIALECT", "postgresql"),
        ("SUPERSET_DB_HOST", "superset_db"),
        ("SUPERSET_DB_PORT", "5432"),
        ("SUPERSET_DB_NAME", "superset"),
        ("SUPERSET_DB_USERNAME", "superset"),
        ("SUPERSET_OAUTH2_BASE_URL", "{% if ENABLE_HTTPS %}https{% else %}http{% endif %}://{{ LMS_HOST }}:8000"),
        ("SUPERSET_OAUTH2_ACCESS_TOKEN_URL", "{{ SUPERSET_OAUTH2_BASE_URL }}/oauth2/access_token/"),
        ("SUPERSET_OAUTH2_AUTHORIZE_URL", "{{ SUPERSET_OAUTH2_BASE_URL }}/oauth2/authorize/"),
        ("SUPERSET_OPENEDX_USERNAME_URL", "{{ SUPERSET_OAUTH2_BASE_URL }}/api/user/v1/me"),
        ("SUPERSET_OPENEDX_USER_PROFILE_URL", "{{ SUPERSET_OAUTH2_BASE_URL }}/api/user/v1/accounts/{username}"),
        ("SUPERSET_OPENEDX_COURSES_LIST_URL",
         "{{ SUPERSET_OAUTH2_BASE_URL }}/api/courses/v1/courses/?permissions={permission}&username={username}"),
        # This admin account is unusable when SSO is enabled,
        # but it's used by the "load examples" optional script.
        ("SUPERSET_ADMIN_USERNAME", "admin"),
        ("SUPERSET_LOAD_EXAMPLES", 0),
    ]
)

hooks.Filters.CONFIG_UNIQUE.add_items(
    [
        # Add settings that don't have a reasonable default for all users here.
        # For instance: passwords, secret keys, etc.
        # Each new setting is a pair: (setting_name, unique_generated_value).
        # Prefix your setting names with 'SUPERSET_'.
        # For example:
        ("SUPERSET_SECRET_KEY", "{{ 24|random_string }}"),
        ("SUPERSET_DB_PASSWORD", "{{ 24|random_string }}"),
        ("SUPERSET_OAUTH2_CLIENT_ID", "{{ 16|random_string }}"),
        ("SUPERSET_OAUTH2_CLIENT_SECRET", "{{ 16|random_string }}"),
        ("SUPERSET_ADMIN_PASSWORD", "{{ 10|random_string }}"),
    ]
)

hooks.Filters.CONFIG_OVERRIDES.add_items(
    [
        # Danger zone!
        # Add values to override settings from Tutor core or other plugins here.
        # Each override is a pair: (setting_name, new_value). For example:
        # ("PLATFORM_NAME", "My platform"),
    ]
)


########################################
# INITIALIZATION TASKS
########################################

# To add a custom initialization task, create a bash script template under:
# tutorsuperset/templates/superset/jobs/init/
# and then add it to the MY_INIT_TASKS list. Each task is in the format:
# ("<service>", ("<path>", "<to>", "<script>", "<template>"))
MY_INIT_TASKS = [
    # For example, to add LMS initialization steps, you could add the script template at:
    # tutorsuperset/templates/superset/jobs/init/lms.sh
    # And then add the line:
    ### ("lms", ("superset", "jobs", "init", "lms.sh")),
    ("superset", ("superset", "jobs", "init", "init-superset.sh")),
    ("lms", ("superset", "jobs", "init", "init-openedx.sh")),
]

# For each task added to MY_INIT_TASKS, we load the task template
# and add it to the CLI_DO_INIT_TASKS filter, which tells Tutor to
# run it as part of the `init` job.
for service, template_path in MY_INIT_TASKS:
    full_path: str = pkg_resources.resource_filename(
        "tutorsuperset", os.path.join("templates", *template_path)
    )
    with open(full_path, encoding="utf-8") as init_task_file:
        init_task: str = init_task_file.read()
    hooks.Filters.CLI_DO_INIT_TASKS.add_item((service, init_task))


########################################
# DOCKER IMAGE MANAGEMENT
########################################

# To build an image with `tutor images build myimage`, add a Dockerfile to templates/superset/build/myimage and write:
# hooks.Filters.IMAGES_BUILD.add_item((
#     "myimage",
#     ("plugins", "superset", "build", "myimage"),
#     "docker.io/myimage:{{ SUPERSET_VERSION }}",
#     (),
# )

# To pull/push an image with `tutor images pull myimage` and `tutor images push myimage`, write:
# hooks.Filters.IMAGES_PULL.add_item((
#     "myimage",
#     "docker.io/myimage:{{ SUPERSET_VERSION }}",
# )
# hooks.Filters.IMAGES_PUSH.add_item((
#     "myimage",
#     "docker.io/myimage:{{ SUPERSET_VERSION }}",
# )


########################################
# TEMPLATE RENDERING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

hooks.Filters.ENV_TEMPLATE_ROOTS.add_items(
    # Root paths for template files, relative to the project root.
    [
        pkg_resources.resource_filename("tutorsuperset", "templates"),
    ]
)

hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    # For each pair (source_path, destination_path):
    # templates at ``source_path`` (relative to your ENV_TEMPLATE_ROOTS) will be
    # rendered to ``source_path/destination_path`` (relative to your Tutor environment).
    # For example, ``tutorsuperset/templates/superset/build``
    # will be rendered to ``$(tutor config printroot)/env/plugins/superset/build``.
    [
        ("superset/build", "plugins"),
        ("superset/apps", "plugins"),
    ],
)

# docker-compose statements shared between the superset services
SUPERSET_DOCKER_COMPOSE_SHARED = """image: apache/superset:{{ SUPERSET_TAG }}
  environment:
    DATABASE_DIALECT: {{ SUPERSET_DB_DIALECT }}
    DATABASE_HOST: {{ SUPERSET_DB_HOST }}
    DATABASE_PORT: {{ SUPERSET_DB_PORT }}
    DATABASE_DB: {{ SUPERSET_DB_NAME }}
    DATABASE_HOST: {{ SUPERSET_DB_HOST }}
    DATABASE_PASSWORD: {{ SUPERSET_DB_PASSWORD }}
    DATABASE_USER: {{ SUPERSET_DB_USERNAME }}
    OPENEDX_MYSQL_HOST: {{ MYSQL_HOST }}
    OPENEDX_MYSQL_PORT: {{ MYSQL_PORT }}
    OPENEDX_MYSQL_DATABASE: {{ OPENEDX_MYSQL_DATABASE }}
    OPENEDX_MYSQL_USERNAME: {{ OPENEDX_MYSQL_USERNAME }}
    OPENEDX_MYSQL_PASSWORD: {{ OPENEDX_MYSQL_PASSWORD }}
    OAUTH2_CLIENT_ID: {{ SUPERSET_OAUTH2_CLIENT_ID }}
    OAUTH2_CLIENT_SECRET: {{ SUPERSET_OAUTH2_CLIENT_SECRET }}
    OAUTH2_BASE_URL: {{ SUPERSET_OAUTH2_BASE_URL }}
    OAUTH2_ACCESS_TOKEN_URL: {{ SUPERSET_OAUTH2_ACCESS_TOKEN_URL }}
    OAUTH2_AUTHORIZE_URL: {{ SUPERSET_OAUTH2_AUTHORIZE_URL }}
    OPENEDX_USERNAME_URL: {{ SUPERSET_OPENEDX_USERNAME_URL }}
    OPENEDX_USER_PROFILE_URL: {{ SUPERSET_OPENEDX_USER_PROFILE_URL }}
    OPENEDX_COURSES_LIST_URL: {{ SUPERSET_OPENEDX_COURSES_LIST_URL }}
    SECRET_KEY: {{ SUPERSET_SECRET_KEY }}
    PYTHONPATH: /app/pythonpath:/app/docker/pythonpath_dev
    REDIS_HOST: superset_cache
    REDIS_PORT: 6379
    FLASK_ENV: production
    SUPERSET_ENV: production
    SUPERSET_LOAD_EXAMPLES: {{ SUPERSET_LOAD_EXAMPLES }}
    SUPERSET_PORT: {{ SUPERSET_PORT }}
    ADMIN_USERNAME: {{ SUPERSET_ADMIN_USERNAME }}
    ADMIN_PASSWORD: {{ SUPERSET_ADMIN_PASSWORD }}
    CYPRESS_CONFIG: 0
  user: root
  depends_on:
    - superset-db
    - superset-cache
  volumes:
    - ../../env/plugins/superset/apps/docker:/app/docker
    - ../../env/plugins/superset/apps/pythonpath:/app/pythonpath
    - ../../env/plugins/superset/apps/superset_home:/app/superset_home
  restart: unless-stopped"""

# Modified from https://github.com/apache/superset/blob/969c963/docker-compose-non-dev.yml
hooks.Filters.ENV_PATCHES.add_item(
    (
        "local-docker-compose-services",
        f"""
superset-cache:
  image: redis:latest
  container_name: superset_cache
  restart: unless-stopped
  volumes:
    - ../../data/superset/redis:/data

superset-db:
  environment:
    POSTGRES_DB: {{{{ SUPERSET_DB_NAME }}}}
    POSTGRES_USER: {{{{ SUPERSET_DB_USERNAME }}}}
    POSTGRES_PASSWORD: {{{{ SUPERSET_DB_PASSWORD }}}}
  image: postgres:10
  container_name: superset_db
  restart: unless-stopped
  volumes:
    - ../../data/superset/postgresql:/var/lib/postgresql/data

superset-app:
  {SUPERSET_DOCKER_COMPOSE_SHARED}
  container_name: superset_app
  command: ["bash", "/app/docker/docker-bootstrap.sh", "app-gunicorn"]
  ports:
    - 8088:{{{{ SUPERSET_PORT }}}}

superset-worker:
  {SUPERSET_DOCKER_COMPOSE_SHARED}
  container_name: superset_worker
  command: ["bash", "/app/docker/docker-bootstrap.sh", "worker"]
  healthcheck:
    test: ["CMD-SHELL", "celery inspect ping -A superset.tasks.celery_app:app -d celery@$$HOSTNAME"]

superset-worker-beat:
  {SUPERSET_DOCKER_COMPOSE_SHARED}
  container_name: superset_worker_beat
  command: ["bash", "/app/docker/docker-bootstrap.sh", "worker"]
  healthcheck:
    disable: true

# All the superset services we need to run together
superset:
  {SUPERSET_DOCKER_COMPOSE_SHARED}
  command: ["bash"]
  depends_on:
    - superset-app
    - superset-worker
    - superset-worker-beat
        """
    )
)

# Initialization jobs
hooks.Filters.ENV_PATCHES.add_item(
    (
        "local-docker-compose-jobs-services",
        f"""
superset-job:
  {SUPERSET_DOCKER_COMPOSE_SHARED}
  depends_on:
    - superset
        """
    )
)


########################################
# PATCH LOADING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

# For each file in tutorsuperset/patches,
# apply a patch based on the file's name and contents.
for path in glob(
    os.path.join(
        pkg_resources.resource_filename("tutorsuperset", "patches"),
        "*",
    )
):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))
