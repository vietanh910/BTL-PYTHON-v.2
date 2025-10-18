import os
import sqlite3
import time
from app import app, DB_FILE, NOTES_DIR


def db_fetchone(query, params=()):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchone()


def run():
    client = app.test_client()

    # Login as demo user created by migration (username=demo, password=demo)
    resp = client.post('/login', data={'username': 'demo', 'password': 'demo'}, follow_redirects=True)
    assert resp.status_code == 200, f"login failed: {resp.status_code}"

    # Find demo user id
    user_row = db_fetchone("SELECT id FROM users WHERE username = ?", ("demo",))
    assert user_row, "Demo user not found in DB"
    user_id = user_row[0]

    suffix = str(int(time.time()))
    folder_name = f"TestDel_{suffix}"
    note_title1 = f"TestNote1_{suffix}"
    note_title2 = f"TestNote2_{suffix}"

    # 1) Create folder
    resp = client.post('/add_folder', data={'name': folder_name}, follow_redirects=True)
    assert resp.status_code == 200, f"add_folder failed: {resp.status_code}"

    folder_row = db_fetchone("SELECT id FROM folders WHERE name = ? AND user_id = ?", (folder_name, user_id))
    assert folder_row is not None, "Folder not inserted in DB"
    folder_id = folder_row[0]

    # 2) Create first note
    resp = client.post('/add_note', data={'title': note_title1, 'folder_id': str(folder_id)}, follow_redirects=True)
    assert resp.status_code == 200, f"add_note 1 failed: {resp.status_code}"

    note1_row = db_fetchone("SELECT id, filename FROM notes WHERE title = ? AND user_id = ?", (note_title1, user_id))
    assert note1_row is not None, "Note1 not found in DB"
    note1_id, note1_filename = note1_row
    file1_path = os.path.join(NOTES_DIR, note1_filename)
    assert os.path.exists(file1_path), "Note1 file not created"

    # 3) Delete note1
    resp = client.post(f'/delete/{note1_id}', follow_redirects=True)
    assert resp.status_code == 200, f"delete_note failed: {resp.status_code}"
    row = db_fetchone("SELECT id FROM notes WHERE id = ? AND user_id = ?", (note1_id, user_id))
    assert row is None, "Note1 row still exists after deletion"
    assert not os.path.exists(file1_path), "Note1 file still exists after deletion"

    # 4) Create second note then delete the whole folder, should also remove note2's file
    resp = client.post('/add_note', data={'title': note_title2, 'folder_id': str(folder_id)}, follow_redirects=True)
    assert resp.status_code == 200, f"add_note 2 failed: {resp.status_code}"

    note2_row = db_fetchone("SELECT id, filename FROM notes WHERE title = ? AND user_id = ?", (note_title2, user_id))
    assert note2_row is not None, "Note2 not found in DB"
    note2_id, note2_filename = note2_row
    file2_path = os.path.join(NOTES_DIR, note2_filename)
    assert os.path.exists(file2_path), "Note2 file not created"

    # Delete folder
    resp = client.post(f'/delete_folder/{folder_id}', follow_redirects=True)
    assert resp.status_code == 200, f"delete_folder failed: {resp.status_code}"

    folder_check = db_fetchone("SELECT id FROM folders WHERE id = ? AND user_id = ?", (folder_id, user_id))
    assert folder_check is None, "Folder still exists in DB after deletion"

    note2_check = db_fetchone("SELECT id FROM notes WHERE id = ? AND user_id = ?", (note2_id, user_id))
    assert note2_check is None, "Note2 still exists in DB after folder deletion"
    assert not os.path.exists(file2_path), "Note2 file still exists after folder deletion"

    print("SMOKE TEST PASSED (auth): create/delete folder and notes including files work.")


if __name__ == '__main__':
    run()
