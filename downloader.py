from huggingface_hub import snapshot_download

if __name__ == '__main__':
    snapshot_download(repo_id="facebook/musicgen-melody-large")
