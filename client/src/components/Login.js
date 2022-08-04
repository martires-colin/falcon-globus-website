import React, { useState, useEffect } from 'react'

export const Login = () => {

    const [authURL, setAuthURL] = useState([])

    useEffect(() => {
        fetch("/auth_url")
          .then(res => res.json())
          .then(
            (result) => {
              setAuthURL(result);
            }
          )
      }, [])

    return (
        <div>
            <h1>Welcome to Falcon</h1>
            <a href={authURL.auth_url}>
                <button>Login</button>
            </a>
            {/* <p>{authURL.auth_url}</p> */}
        </div>
    )
}

