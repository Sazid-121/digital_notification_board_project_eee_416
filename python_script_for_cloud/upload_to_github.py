from github import Github

def upload_files_to_github(token, repo_name, branch="main"):
    files = [
        {
            "local_path": "version.txt",
            "repo_path": "version.txt",
            "binary": False
        },
        {
            "local_path": "display_image_rgb565.bin",
            "repo_path": "display_image_rgb565.bin",
            "binary": True
        },
        # Optional: Uncomment if you use display_info.txt
        # {
        #     "local_path": "display_info.txt",
        #     "repo_path": "display_info.txt",
        #     "binary": False
        # }
    ]

    try:
        github = Github(token)
        repo = github.get_repo(repo_name)

        for file in files:
            mode = "rb" if file["binary"] else "r"
            with open(file["local_path"], mode) as f:
                content = f.read()
                if not file["binary"]:
                    content = content.strip()

            try:
                existing_file = repo.get_contents(file["repo_path"], ref=branch)
                sha = existing_file.sha

                repo.update_file(
                    path=file["repo_path"],
                    message=f"Update {file['repo_path']} from script",
                    content=content,
                    sha=sha,
                    branch=branch
                )
                print(f"✅ Updated: {file['repo_path']}")

            except Exception:
                # If the file does not exist yet, create it
                repo.create_file(
                    path=file["repo_path"],
                    message=f"Create {file['repo_path']} from script",
                    content=content,
                    branch=branch
                )
                print(f"🆕 Created: {file['repo_path']}")

    except Exception as e:
        print(f"❌ GitHub upload failed: {e}")
