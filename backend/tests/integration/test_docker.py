"""
Testes de validacao da configuracao Docker
"""
import pytest
import os
from pathlib import Path


# Root do projeto (DEV_ETL)
ROOT_DIR = Path(__file__).parent.parent.parent.parent


class TestDockerFilesExist:
    """Testa se todos os arquivos Docker existem"""

    def test_docker_compose_exists(self):
        """docker-compose.yml deve existir na raiz"""
        assert (ROOT_DIR / "docker-compose.yml").exists()

    def test_backend_dockerfile_exists(self):
        """backend/Dockerfile deve existir"""
        assert (ROOT_DIR / "backend" / "Dockerfile").exists()

    def test_frontend_dockerfile_exists(self):
        """frontend/Dockerfile deve existir"""
        assert (ROOT_DIR / "frontend" / "Dockerfile").exists()

    def test_frontend_nginx_conf_exists(self):
        """frontend/nginx.conf deve existir"""
        assert (ROOT_DIR / "frontend" / "nginx.conf").exists()

    def test_env_example_exists(self):
        """.env.example deve existir na raiz"""
        assert (ROOT_DIR / ".env.example").exists()

    def test_backend_dockerignore_exists(self):
        """backend/.dockerignore deve existir"""
        assert (ROOT_DIR / "backend" / ".dockerignore").exists()

    def test_frontend_dockerignore_exists(self):
        """frontend/.dockerignore deve existir"""
        assert (ROOT_DIR / "frontend" / ".dockerignore").exists()


class TestDockerComposeContent:
    """Testa o conteudo do docker-compose.yml"""

    @pytest.fixture
    def compose_content(self):
        """Le o conteudo do docker-compose.yml"""
        with open(ROOT_DIR / "docker-compose.yml", "r") as f:
            return f.read()

    def test_has_backend_service(self, compose_content):
        """Deve ter servico backend"""
        assert "backend:" in compose_content

    def test_has_frontend_service(self, compose_content):
        """Deve ter servico frontend"""
        assert "frontend:" in compose_content

    def test_backend_port_4001(self, compose_content):
        """Backend deve expor porta 4001"""
        assert "4001:4001" in compose_content or "4001" in compose_content

    def test_frontend_port_4000(self, compose_content):
        """Frontend deve expor porta 4000"""
        assert "4000:80" in compose_content or "4000" in compose_content

    def test_has_volumes(self, compose_content):
        """Deve ter volumes para persistencia"""
        assert "volumes:" in compose_content

    def test_has_healthcheck(self, compose_content):
        """Deve ter healthcheck configurado"""
        assert "healthcheck:" in compose_content or "health" in compose_content


class TestBackendDockerfile:
    """Testa o conteudo do Dockerfile do backend"""

    @pytest.fixture
    def dockerfile_content(self):
        """Le o conteudo do Dockerfile"""
        with open(ROOT_DIR / "backend" / "Dockerfile", "r") as f:
            return f.read()

    def test_uses_python_image(self, dockerfile_content):
        """Deve usar imagem Python"""
        assert "python:" in dockerfile_content.lower()

    def test_has_workdir(self, dockerfile_content):
        """Deve ter WORKDIR definido"""
        assert "WORKDIR" in dockerfile_content

    def test_copies_requirements(self, dockerfile_content):
        """Deve copiar requirements.txt"""
        assert "requirements.txt" in dockerfile_content

    def test_installs_dependencies(self, dockerfile_content):
        """Deve instalar dependencias com pip"""
        assert "pip install" in dockerfile_content

    def test_exposes_port(self, dockerfile_content):
        """Deve expor porta"""
        assert "EXPOSE" in dockerfile_content

    def test_has_cmd_or_entrypoint(self, dockerfile_content):
        """Deve ter CMD ou ENTRYPOINT"""
        assert "CMD" in dockerfile_content or "ENTRYPOINT" in dockerfile_content


class TestFrontendDockerfile:
    """Testa o conteudo do Dockerfile do frontend"""

    @pytest.fixture
    def dockerfile_content(self):
        """Le o conteudo do Dockerfile"""
        with open(ROOT_DIR / "frontend" / "Dockerfile", "r") as f:
            return f.read()

    def test_uses_node_image(self, dockerfile_content):
        """Deve usar imagem Node"""
        assert "node:" in dockerfile_content.lower()

    def test_uses_multistage_build(self, dockerfile_content):
        """Deve usar multi-stage build"""
        assert dockerfile_content.count("FROM") >= 2

    def test_uses_nginx(self, dockerfile_content):
        """Deve usar nginx para producao"""
        assert "nginx" in dockerfile_content.lower()

    def test_runs_npm_build(self, dockerfile_content):
        """Deve rodar npm build"""
        assert "npm run build" in dockerfile_content or "npm ci" in dockerfile_content

    def test_copies_dist(self, dockerfile_content):
        """Deve copiar arquivos de build"""
        assert "COPY --from" in dockerfile_content


class TestNginxConfig:
    """Testa o conteudo do nginx.conf"""

    @pytest.fixture
    def nginx_content(self):
        """Le o conteudo do nginx.conf"""
        with open(ROOT_DIR / "frontend" / "nginx.conf", "r") as f:
            return f.read()

    def test_listens_on_port_80(self, nginx_content):
        """Deve escutar na porta 80"""
        assert "listen 80" in nginx_content

    def test_has_api_proxy(self, nginx_content):
        """Deve ter proxy para /api"""
        assert "/api" in nginx_content
        assert "proxy_pass" in nginx_content

    def test_has_websocket_proxy(self, nginx_content):
        """Deve ter proxy para WebSocket"""
        assert "/ws" in nginx_content
        assert "upgrade" in nginx_content.lower()

    def test_has_spa_routing(self, nginx_content):
        """Deve ter roteamento SPA (try_files)"""
        assert "try_files" in nginx_content
        assert "index.html" in nginx_content

    def test_has_gzip(self, nginx_content):
        """Deve ter compressao gzip"""
        assert "gzip" in nginx_content


class TestEnvExample:
    """Testa o conteudo do .env.example"""

    @pytest.fixture
    def env_content(self):
        """Le o conteudo do .env.example"""
        with open(ROOT_DIR / ".env.example", "r") as f:
            return f.read()

    def test_has_etl_host(self, env_content):
        """Deve ter ETL_HOST"""
        assert "ETL_HOST" in env_content

    def test_has_etl_port(self, env_content):
        """Deve ter ETL_PORT"""
        assert "ETL_PORT" in env_content

    def test_has_vite_api_url(self, env_content):
        """Deve ter VITE_API_URL"""
        assert "VITE_API_URL" in env_content

    def test_has_vite_ws_url(self, env_content):
        """Deve ter VITE_WS_URL"""
        assert "VITE_WS_URL" in env_content

    def test_has_cors_origins(self, env_content):
        """Deve ter ETL_CORS_ORIGINS"""
        assert "ETL_CORS_ORIGINS" in env_content


class TestDockerIgnore:
    """Testa o conteudo dos .dockerignore"""

    def test_backend_ignores_pycache(self):
        """Backend deve ignorar __pycache__"""
        content = (ROOT_DIR / "backend" / ".dockerignore").read_text()
        assert "__pycache__" in content

    def test_backend_ignores_tests(self):
        """Backend deve ignorar tests/"""
        content = (ROOT_DIR / "backend" / ".dockerignore").read_text()
        assert "tests" in content.lower()

    def test_frontend_ignores_node_modules(self):
        """Frontend deve ignorar node_modules"""
        content = (ROOT_DIR / "frontend" / ".dockerignore").read_text()
        assert "node_modules" in content

    def test_frontend_ignores_dist(self):
        """Frontend deve ignorar dist/"""
        content = (ROOT_DIR / "frontend" / ".dockerignore").read_text()
        assert "dist" in content
