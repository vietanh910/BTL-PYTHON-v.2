import time
import sqlite3
from app import app, DB_FILE


def db_fetchone(query, params=()):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchone()


def run():
    client = app.test_client()
    ts = str(int(time.time()))
    userA = f"userA_{ts}"
    userB = f"userB_{ts}"
    pwd = "secret123"

    # Register user A (auto-logged-in)
    resp = client.post('/register', data={'username': userA, 'password': pwd}, follow_redirects=True)
    assert resp.status_code == 200, f"register A failed: {resp.status_code}"
    rowA = db_fetchone("SELECT id FROM users WHERE username=?", (userA,))
    assert rowA, "User A missing in DB"
    uidA = rowA[0]

    # Create a folder and note for A
    folder_name = f"FolderA_{ts}"
    note_title = f"NoteA_{ts}"
    resp = client.post('/add_folder', data={'name': folder_name}, follow_redirects=True)
    assert resp.status_code == 200
    folderA = db_fetchone("SELECT id FROM folders WHERE name=? AND user_id=?", (folder_name, uidA))
    assert folderA, "Folder A missing"
    fidA = folderA[0]

    resp = client.post('/add_note', data={'title': note_title, 'folder_id': str(fidA)}, follow_redirects=True)
    assert resp.status_code == 200
    noteA = db_fetchone("SELECT id FROM notes WHERE title=? AND user_id=?", (note_title, uidA))
    assert noteA, "Note A missing"
    nidA = noteA[0]

    # Logout A
    client.get('/logout', follow_redirects=True)

    # Register user B (auto-logged-in)
    resp = client.post('/register', data={'username': userB, 'password': pwd}, follow_redirects=True)
    assert resp.status_code == 200
    rowB = db_fetchone("SELECT id FROM users WHERE username=?", (userB,))
    assert rowB, "User B missing in DB"
    uidB = rowB[0]

    # Try to access A's note as B (should be 404)
    resp = client.get(f'/note/{nidA}', follow_redirects=False)
    assert resp.status_code == 404, f"User B could access User A's note (status {resp.status_code})"

    # Try to delete A's folder as B (should not delete)
    resp = client.post(f'/delete_folder/{fidA}', follow_redirects=True)
    # Check folder still exists for A
    folderA_check = db_fetchone("SELECT id FROM folders WHERE id=? AND user_id=?", (fidA, uidA))
    assert folderA_check is not None, "User B deleted User A's folder"

    print("AUTH ISOLATION TEST PASSED: Users are isolated and cannot access/delete each other's data.")


if __name__ == '__main__':
    run()

