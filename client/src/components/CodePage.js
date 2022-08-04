import React, { useState, useEffect } from 'react'

export const CodePage = () => {
  
    const QueryString = window.location.search
    const urlParams = new URLSearchParams(QueryString)
    const auth_code = urlParams.get('code')
  
    const [tokens, setTokens] = useState([])

    useEffect(() => {
        fetch(`/get_tokens/${auth_code}`)
          .then(res => res.json())
          .then(
            (result) => {
              setTokens(result);
            }
          )
      }, [])

    return (
    <div>
        {tokens.globus_auth_code}
    </div>
    
  )
}
