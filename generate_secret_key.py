#!/usr/bin/env python3
import secrets
import base64
import os
from dotenv import load_dotenv

def generate_secret_key(length=32):
    """Generate a secure random key with the specified length"""
    return secrets.token_hex(length)

def generate_base64_secret_key(length=32):
    """Generate a URL-safe base64 encoded secret key"""
    return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode('utf-8')

def update_env_file(secret_key):
    """Updates the .env file with the new secret key if it exists"""
    env_file = ".env"
    
    # Check if .env file exists, create from example if not
    if not os.path.exists(env_file):
        if os.path.exists(".env.example"):
            print(f"Creating {env_file} from .env.example")
            with open(".env.example", "r") as example_file:
                example_content = example_file.read()
            
            # Replace the example secret key with our new one
            updated_content = example_content.replace(
                "SECRET_KEY=your-secret-key-for-jwt", 
                f"SECRET_KEY={secret_key}"
            )
            
            with open(env_file, "w") as env_file_obj:
                env_file_obj.write(updated_content)
            
            print(f"Created {env_file} with new secret key")
            return True
        else:
            print(".env file does not exist and could not find .env.example")
            return False
    
    # If .env exists, try to update the SECRET_KEY
    load_dotenv()
    current_key = os.getenv("SECRET_KEY")
    
    if current_key:
        with open(env_file, "r") as file:
            content = file.read()
        
        # Replace the current secret key with the new one
        updated_content = content.replace(
            f"SECRET_KEY={current_key}", 
            f"SECRET_KEY={secret_key}"
        )
        
        with open(env_file, "w") as file:
            file.write(updated_content)
        
        print(f"Updated SECRET_KEY in {env_file}")
        return True
    else:
        print("SECRET_KEY not found in .env file")
        # Append the SECRET_KEY if it doesn't exist
        with open(env_file, "a") as file:
            file.write(f"\nSECRET_KEY={secret_key}\n")
        print(f"Appended SECRET_KEY to {env_file}")
        return True

if __name__ == "__main__":
    # Generate different types of keys
    hex_key = generate_secret_key()
    base64_key = generate_base64_secret_key()
    
    print("\n=== Secret Key Generator ===")
    print("\nGenerated secret keys:")
    print(f"Hex key (64 characters): {hex_key}")
    print(f"Base64 key (43 characters): {base64_key}")
    
    # Ask user which key to use
    print("\nWhich key would you like to use?")
    print("1: Hex key")
    print("2: Base64 key")
    print("3: Generate a new key")
    print("4: Just show keys, don't update files")
    
    choice = input("\nEnter choice (1-4): ")
    
    if choice == "1":
        selected_key = hex_key
    elif choice == "2":
        selected_key = base64_key
    elif choice == "3":
        key_length = int(input("Enter key length in bytes (default 32): ") or 32)
        selected_key = generate_secret_key(key_length)
    elif choice == "4":
        print("No files updated.")
        exit(0)
    else:
        print("Invalid choice. Exiting.")
        exit(1)
    
    # Confirm before updating
    confirm = input(f"\nUpdate .env file with this key?\n{selected_key}\n\n(y/n): ")
    
    if confirm.lower() in ["y", "yes"]:
        update_env_file(selected_key)
        print("\nDone! Your application is now more secure.")
    else:
        print("\nKey generated but not saved to any file:")
        print(selected_key)
        print("\nCopy this key and update your .env file manually if needed.") 