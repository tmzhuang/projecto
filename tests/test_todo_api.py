from __future__ import absolute_import

from projecto.models import Todo

import unittest
from .utils import ProjectTestCase

class TestTodoAPI(ProjectTestCase):
  def base_url(self, postfix):
    return "/api/v1/projects/{}/todos{}".format(self.project_key, postfix)

  # We need to test for security problems like XSS here.

  def test_new_todo(self):
    self.login()
    response, data = self.postJSON(self.base_url("/"), data={"title": "A title"})

    self.assertStatus(200, response)
    self.assertTrue("key" in data)
    self.assertTrue("title" in data)
    self.assertEquals("A title", data["title"])
    self.assertTrue("author" in data)
    self.assertEquals(self.user.key, data["author"]["key"])

    response, data = self.postJSON(self.base_url("/"), data={"title": "A title", "content": "some content", "tags": ["a", "b", "c"]})
    self.assertStatus(200, response)
    self.assertTrue("key" in data)
    self.assertTrue("title" in data)
    self.assertEquals("A title", data["title"])
    self.assertTrue("author" in data)
    self.assertEquals(self.user.key, data["author"]["key"])
    self.assertTrue("content" in data)
    self.assertTrue("markdown" in data["content"])
    self.assertEquals("some content", data["content"]["markdown"])
    self.assertTrue("html" in data["content"])
    self.assertTrue("<p>some content</p>" in data["content"]["html"])
    self.assertTrue("tags" in data)
    self.assertEquals(["a", "b", "c"], data["tags"])

  def test_new_todo_reject_badrequest(self):
    self.login()
    response, data = self.postJSON(self.base_url("/"), data={"invalid": "invald"})
    self.assertStatus(400, response)

    self.postJSON(self.base_url("/"), data={"title": "title", "content": "content", "author": "invalid"})
    self.assertStatus(400, response)

  def test_new_todo_reject_permission(self):
    response, data = self.postJSON(self.base_url("/"), data={"title": "todo"})
    self.assertStatus(403, response)

    user2 = self.create_user("test2@test.com")
    self.login(user2)
    response, data = self.postJSON(self.base_url("/"), data={"title": "todo"})
    self.assertStatus(403, response)

  # TODO: this method
  # def test_new_todo_filter_xss(self):

  def test_update_todo(self):
    self.login()
    response, data = self.postJSON(self.base_url("/"), data={"title": "todo"})
    key = data["key"]

    response, data = self.putJSON(self.base_url("/" + key), data={"title": "todo2"})
    self.assertStatus(200, response)
    self.assertTrue("key" in data)
    self.assertEquals(key, data["key"])
    self.assertEquals("todo2", data["title"])

    response, data = self.putJSON(self.base_url("/" + key), data={"content": {"markdown": "aaaa"}})
    self.assertStatus(200, response)
    self.assertEquals("todo2", data["title"])
    self.assertTrue("content" in data)
    self.assertTrue("markdown" in data["content"])
    self.assertEquals("aaaa", data["content"]["markdown"])
    self.assertTrue("<p>aaaa</p>" in data["content"]["html"])

  def test_update_todo_reject_badrequest(self):
    self.login()
    response, data = self.postJSON(self.base_url("/"), data={"title": "todo"})
    key = data["key"]

    response, data = self.putJSON(self.base_url("/" + key), data={"author": "someauthor"})
    self.assertStatus(400, response)

    response, data = self.putJSON(self.base_url("/" + key), data={"title": "title", "adfaf": "adfa"})
    self.assertStatus(400, response)

  def test_update_todo_reject_permission(self):
    self.login()
    response, data = self.postJSON(self.base_url("/"), data={"title": "todo"})
    key = data["key"]

    self.logout()
    response, data = self.putJSON(self.base_url("/" + key), data={"title": "todo2"})
    self.assertStatus(403, response)

    user2 = self.create_user("test2@test.com")
    self.login(user2)
    response, data = self.putJSON(self.base_url("/" + key), data={"title": "todo2"})
    self.assertStatus(403, response)

  def test_get_todo(self):
    self.login()
    response, data = self.postJSON(self.base_url("/"), data={"title": "todo"})
    key = data["key"]

    response, data = self.getJSON(self.base_url("/" + key))
    self.assertStatus(200, response)

  def test_get_todo_reject_permission(self):
    self.login()
    response, data = self.postJSON(self.base_url("/"), data={"title": "todo"})
    key = data["key"]
    self.logout()

    response, data = self.getJSON(self.base_url("/" + key))
    self.assertStatus(403, response)

    user2 = self.create_user("test2@test.com")
    self.login(user2)
    response, data = self.getJSON(self.base_url("/" + key))
    self.assertStatus(403, response)

  def test_markdone_todo(self):
    self.login()
    response, data = self.postJSON(self.base_url("/"), data={"title": "todo"})
    key = data["key"]

    response, data = self.postJSON(self.base_url("/" + key + "/markdone"), data={"done": True})
    self.assertStatus(200, response)
    todo = Todo.get(key)
    self.assertTrue(todo.done)

    response, data = self.postJSON(self.base_url("/" + key + "/markdone"), data={"done": False})
    self.assertStatus(200, response)
    todo = Todo.get(key)
    self.assertFalse(todo.done)

  def test_markdone_todo_reject_badrequest(self):
    self.login()
    response, data = self.postJSON(self.base_url("/"), data={"title": "todo"})
    key = data["key"]

    response, data = self.postJSON(self.base_url("/" + key + "/markdone"), data={"notdone": False})
    self.assertStatus(400, response)

    response, data = self.postJSON(self.base_url("/" + key + "/markdone"), data={"done": False, "invalid": "invalid"})
    self.assertStatus(400, response)

  def test_markdone_todo_reject_permission(self):
    self.login()
    response, data = self.postJSON(self.base_url("/"), data={"title": "todo"})
    key = data["key"]
    self.logout()

    response, data = self.postJSON(self.base_url("/" + key + "/markdone"), data={"done": True})
    self.assertStatus(403, response)

    user2 = self.create_user("test2@test.com")
    self.login(user2)
    response, data = self.postJSON(self.base_url("/" + key + "/markdone"), data={"done": True})
    self.assertStatus(403, response)

  def test_index_todos(self):
    self.login()

    keys = []
    for i in xrange(10):
      response, data = self.postJSON(self.base_url("/"), data={"title": "a todo"})
      keys.append(data["key"])

    keys.reserve()

    response, data = self.getJSON(self.base_url("/"), data={"title": "a todo"})



if __name__ == "__main__":
  unittest.main()