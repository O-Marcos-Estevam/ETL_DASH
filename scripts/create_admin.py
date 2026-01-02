#!/usr/bin/env python
"""
Cria o primeiro usuário administrador do sistema.

Uso:
    python scripts/create_admin.py
    python scripts/create_admin.py --username admin --password senha123
    python scripts/create_admin.py --email admin@empresa.com

Este script deve ser executado apenas uma vez para criar o admin inicial.
Após isso, use a API /api/auth/users para gerenciar usuários.
"""
import sys
import os
import getpass
import argparse

# Adicionar paths necessários
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_dir = os.path.join(project_root, "backend")

sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

from auth.database import init_auth_tables, create_user, get_user_by_username
from auth.models import UserRole
from auth.security import get_password_hash


def validate_password(password: str) -> tuple[bool, str]:
    """Valida requisitos mínimos de senha."""
    if len(password) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres"
    if not any(c.isupper() for c in password):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    if not any(c.islower() for c in password):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    if not any(c.isdigit() for c in password):
        return False, "Senha deve conter pelo menos um número"
    return True, ""


def main():
    parser = argparse.ArgumentParser(
        description="Cria o primeiro usuário administrador do sistema"
    )
    parser.add_argument(
        "--username",
        type=str,
        default="admin",
        help="Nome de usuário (padrão: admin)"
    )
    parser.add_argument(
        "--password",
        type=str,
        help="Senha (se não fornecida, será solicitada)"
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Email do administrador (opcional)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescrever se usuário já existir"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("  ETL Dashboard - Criação de Usuário Admin")
    print("=" * 50)
    print()

    # Inicializar tabelas de auth
    print("[1/4] Inicializando banco de dados...")
    init_auth_tables()
    print("      OK - Tabelas de autenticação prontas")
    print()

    # Verificar se usuário já existe
    print(f"[2/4] Verificando usuário '{args.username}'...")
    existing_user = get_user_by_username(args.username)

    if existing_user:
        if args.force:
            print(f"      AVISO: Usuário '{args.username}' já existe (--force ignorado)")
            print("      Para resetar senha, use a API ou delete manualmente do banco")
            return 1
        else:
            print(f"      ERRO: Usuário '{args.username}' já existe!")
            print("      Use --force para tentar sobrescrever ou escolha outro username")
            return 1
    else:
        print("      OK - Usuário disponível")
    print()

    # Obter senha
    print("[3/4] Configurando senha...")
    password = args.password

    if not password:
        while True:
            password = getpass.getpass("      Digite a senha: ")
            password_confirm = getpass.getpass("      Confirme a senha: ")

            if password != password_confirm:
                print("      ERRO: Senhas não coincidem. Tente novamente.")
                continue

            valid, msg = validate_password(password)
            if not valid:
                print(f"      ERRO: {msg}")
                continue

            break
    else:
        valid, msg = validate_password(password)
        if not valid:
            print(f"      ERRO: {msg}")
            return 1

    print("      OK - Senha validada")
    print()

    # Criar usuário
    print("[4/4] Criando usuário admin...")

    try:
        # Hash da senha
        hashed_password = get_password_hash(password)

        # Criar usuário com parâmetros corretos
        user = create_user(
            username=args.username,
            hashed_password=hashed_password,
            email=args.email,
            role=UserRole.ADMIN
        )

        if user:
            print("      OK - Usuário criado com sucesso!")
            print()
            print("=" * 50)
            print("  RESUMO")
            print("=" * 50)
            print(f"  Username: {user.username}")
            print(f"  Role:     {user.role.value}")
            print(f"  Email:    {user.email or '(não definido)'}")
            print(f"  ID:       {user.id}")
            print()
            print("  Acesse o dashboard e faça login com essas credenciais.")
            print("=" * 50)
            return 0
        else:
            print("      ERRO: Falha ao criar usuário (retorno nulo)")
            return 1

    except Exception as e:
        print(f"      ERRO: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
