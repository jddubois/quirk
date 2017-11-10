DELETE FROM quirk_likes;
DELETE FROM quirks;
DELETE FROM matches;
DELETE FROM user_likes;
DELETE FROM deals;
DELETE FROM business;
DELETE FROM photos;
DELETE FROM users;

INSERT INTO users VALUES (1, 'Paul Pal', 21, 'I am the king', 5, 43.1234, 42.1762, 20, 25, 0, 1);
INSERT INTO users VALUES (2, 'Nikki Vartabedian', 22, 'I am the queen', 5, 43.1234, 42.1762, 20, 25, 1, 0);
INSERT INTO users VALUES (3, 'John DuBois', 22, 'The sloth king', 5, 43.1234, 42.1762, 20, 25, 0, 1, 0);
INSERT INTO users VALUES (4, 'Ori Lindner', 22, 'Video game nerd', 5, -43.1234, 42.1762, 20, 25, 0, 1);
INSERT INTO users VALUES (5, 'BILLY', 22, 'No explanation needed for this one...', 5, 43.1234, 42.1762, 20, 25, 0, 1);

INSERT INTO quirks VALUES (1, 'I like long walks on the beach', 1, FALSE);
INSERT INTO quirks VALUES (2, 'I like long walks in the snow', 1, FALSE);
INSERT INTO quirks VALUES (3, 'I like long walks on the moon', 1, FALSE);
INSERT INTO quirks VALUES (4, 'I like long walks on the sun', 1, FALSE);
INSERT INTO quirks VALUES (5, 'I eat ass', 1, TRUE);

INSERT INTO quirks VALUES (6, 'I fart a lot', 2, FALSE);
INSERT INTO quirks VALUES (7, 'I never stop farting', 2, FALSE);
INSERT INTO quirks VALUES (8, 'Literally have an issue with farting', 2, FALSE);
INSERT INTO quirks VALUES (9, 'Could it be because Im lactose intolerant', 2, FALSE);
INSERT INTO quirks VALUES (10, 'YeeeeeeeEEEeEEeEEEeeeEeeeEEE', 2, FALSE);

INSERT INTO quirks VALUES (11, 'ay', 3, FALSE);
INSERT INTO quirks VALUES (12, 'ayy', 3, FALSE);
INSERT INTO quirks VALUES (13, 'ayyy', 3, FALSE);
INSERT INTO quirks VALUES (14, 'ayyyy', 3, FALSE);
INSERT INTO quirks VALUES (15, 'ayyyyy', 3, FALSE);

INSERT INTO matches VALUES ('1', '3');
INSERT INTO photos VALUES ('image', 'png', 3, TRUE);

INSERT INTO business VALUES ('1', 'starbucks@gmail.com', 'password', 'Starbucks');
INSERT INTO business VALUES ('2', 'espresso@gmail.com', 'password', 'Espresso');
INSERT INTO business VALUES ('3', 'savasbayby@gmail.com', 'password', 'Savas');

INSERT INTO deals VALUES (1, 43.1234, 42.1762, 'Starbucks', 1, 'Buy 2 get one 1/2 off', 'Come buy a starbucks drink', 'no_photo.jpg');
INSERT INTO deals VALUES (2, 44.1234, 42.1762, 'Espresso Royale', 2, 'Buy 2 pastries get one 1/3 off', 'Come buy a pastry', 'no_photo.jpg');
INSERT INTO deals VALUES (3, 43.2744, 42.7751, 'Savas', 3, 'Dinner for 2', 'Fancy date leggo', 'no_photo.jpg');
