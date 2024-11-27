# Create new directories
#mkdir -p _data _includes _posts projects pages

# Move existing content
# mv about.md pages/
# mv research.md pages/
# mv CV.md pages/
# mv Pubs.md pages/publications.md

# # Create new files
# touch _data/navigation.yml
# touch _data/publications.yml
# touch _data/projects.yml
# touch _includes/header.html
# touch _includes/footer.html

# bundle exec jekyll clean
# bundle exec jekyll serve --watch --livereload


# Create a new SQLite database
sqlite3 test.db <<EOF
CREATE TABLE products (
  id INTEGER PRIMARY KEY,
  name TEXT,
  price REAL
);

INSERT INTO products (name, price) VALUES
  ('Widget', 19.99),
  ('Gadget', 29.99),
  ('Gizmo', 39.99),
  ('Smart Watch', 199.99),
  ('Wireless Earbuds', 89.99),
  ('Portable Charger', 24.99),
  ('Bluetooth Speaker', 79.99),
  ('Phone Stand', 15.99),
  ('Laptop Sleeve', 34.99),
  ('Mini Drone', 299.99),
  ('LED Desk Lamp', 45.99),
  ('Keyboard', 129.99),
  ('Mouse Pad', 12.99),
  ('USB Hub', 49.99),
  ('Webcam', 69.99),
  ('Screen Protector', 9.99),
  ('Travel Adapter', 27.99),
  ('Gaming Headset', 159.99),
  ('Fitness Tracker', 119.99),
  ('Portable SSD', 179.99);
EOF
